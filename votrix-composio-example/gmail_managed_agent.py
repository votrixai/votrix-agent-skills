"""
Gmail Managed Agent — file-based conversation mode.

How to use:
  Terminal 1:  python app/examples/gmail_managed_agent.py
  Editor:      open input.txt  → type a message → save
  Terminal 2:  tail -f output.txt   (or just open the file)

Flow:
  1. Script watches input.txt (polls every 0.3 s for mtime change).
  2. On save: reads message, clears input.txt, streams reply into output.txt.
  3. Session stays alive → full conversation context across turns.
  4. Write 'quit' in input.txt to stop.

SDK calls:
  client.beta.agents.create()
  client.beta.environments.create()
  client.beta.sessions.create(agent=..., environment_id=...)
  client.beta.sessions.events.stream(session_id)   ← open BEFORE send
  client.beta.sessions.events.send(session_id, events=[...])
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import httpx

# ─────────────────────────────────────────────────────────────────────────────
# File paths
# ─────────────────────────────────────────────────────────────────────────────

_DIR = Path(__file__).parent

INPUT_FILE  = _DIR / "input.txt"    # you write here, cleared after each read
OUTPUT_FILE = _DIR / "output.txt"   # append-only conversation log

_AGENT_ID_FILE = _DIR / ".gmail_agent_id"
_ENV_ID_FILE   = _DIR / ".gmail_env_id"

# ─────────────────────────────────────────────────────────────────────────────
# Agent config
# ─────────────────────────────────────────────────────────────────────────────

COMPOSIO_API_KEY = "ak_OSbHBiWmp39YBwkbKl0O"

# MCP server config has no headers field — auth goes in the URL as query param
COMPOSIO_GMAIL_MCP_URL = (
    "https://backend.composio.dev/v3/mcp"
    "/5a629a28-ec72-4601-b192-cf705ecc6d01"
    f"/mcp?user_id=votrix-claude-managed-agent-test&api_key={COMPOSIO_API_KEY}"
)

# SSE inactivity timeout: if no event arrives for 60 s, raise ReadTimeout.
# (timeout=N alone is a connect timeout; httpx.Timeout.read covers between-chunk silence)
_STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

AGENT_CONFIG = {
    "name": "votrix-gmail-agent",
    "model": "claude-sonnet-4-6",
    "system": (
        "You are a professional Gmail assistant. "
        "You can search, read, draft, and send emails on behalf of the user. "
        "Always confirm before sending. Keep replies concise and professional."
    ),
    "mcp_servers": [
        {"type": "url", "name": "composio_gmail", "url": COMPOSIO_GMAIL_MCP_URL}
    ],
    "tools": [
        # Sandbox: file system, code execution, web fetch — powered by the environment
        {
            "type": "agent_toolset_20260401",
            "default_config": {
                "permission_policy": {"type": "always_allow"},
            },
        },
        # Gmail via Composio MCP
        {
            "type": "mcp_toolset",
            "mcp_server_name": "composio_gmail",
            "default_config": {
                "permission_policy": {"type": "always_allow"},
            },
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _out(text: str, *, flush: bool = False) -> None:
    """Append text to output.txt (and optionally flush immediately)."""
    with OUTPUT_FILE.open("a", encoding="utf-8") as f:
        f.write(text)
        if flush:
            f.flush()


def get_or_create_agent(client: anthropic.Anthropic) -> str:
    if _AGENT_ID_FILE.exists():
        agent_id = _AGENT_ID_FILE.read_text().strip()
        print(f"[agent] {agent_id} (cached)")
        return agent_id
    agent = client.beta.agents.create(**AGENT_CONFIG)
    _AGENT_ID_FILE.write_text(agent.id)
    print(f"[agent] {agent.id} (created v{agent.version})")
    return agent.id


def get_or_create_environment(client: anthropic.Anthropic) -> str:
    if _ENV_ID_FILE.exists():
        env_id = _ENV_ID_FILE.read_text().strip()
        print(f"[env]   {env_id} (cached)")
        return env_id
    env = client.beta.environments.create(
        name="votrix-gmail-env",
        config={"type": "cloud"},
    )
    _ENV_ID_FILE.write_text(env.id)
    print(f"[env]   {env.id} (created)")
    return env.id

# ─────────────────────────────────────────────────────────────────────────────
# File-based conversation loop
# ─────────────────────────────────────────────────────────────────────────────

def run_file_chat(client: anthropic.Anthropic, agent_id: str, env_id: str) -> None:
    # Prepare files
    INPUT_FILE.touch()
    INPUT_FILE.write_text("")

    session = client.beta.sessions.create(agent=agent_id, environment_id=env_id)

    _out(f"{'─'*60}\n")
    _out(f"Session {session.id}  started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    _out(f"Write your message in input.txt and save to send.\n")
    _out(f"{'─'*60}\n\n")

    print(f"[session] {session.id}")
    print(f"[ready]   watching {INPUT_FILE}")
    print(f"[output]  {OUTPUT_FILE}")
    print("Write a message in input.txt and save. Ctrl-C to quit.\n")

    last_mtime = INPUT_FILE.stat().st_mtime

    while True:
        try:
            time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n[bye]")
            _out("\n[session ended]\n")
            break

        try:
            mtime = INPUT_FILE.stat().st_mtime
        except FileNotFoundError:
            continue

        if mtime == last_mtime:
            continue

        last_mtime = mtime
        user_input = INPUT_FILE.read_text(encoding="utf-8").strip()

        if not user_input:
            continue

        # Quit signal
        if user_input.lower() in ("quit", "exit", "q"):
            print("[bye]")
            _out("\n[session ended]\n")
            break

        # Clear input immediately so user knows it was consumed
        INPUT_FILE.write_text("")
        last_mtime = INPUT_FILE.stat().st_mtime

        # Write user turn to output
        _out(f"[{_ts()}] You: {user_input}\n\n")
        _out(f"[{_ts()}] Agent: ", flush=True)
        print(f"[{_ts()}] → processing...")

        # When the agent calls an MCP tool, Anthropic executes it asynchronously
        # and the SSE stream may close mid-turn. We reconnect until status_idle.
        idle = False
        first = True
        try:
            while not idle:
                with client.beta.sessions.events.stream(
                    session.id, timeout=_STREAM_TIMEOUT
                ) as stream:
                    if first:
                        client.beta.sessions.events.send(
                            session.id,
                            events=[
                                {
                                    "type": "user.message",
                                    "content": [{"type": "text", "text": user_input}],
                                }
                            ],
                        )
                        first = False
                    for event in stream:
                        match event.type:
                            case "agent.message":
                                for block in event.content:
                                    if block.type == "text":
                                        _out(block.text, flush=True)
                            case "agent.mcp_tool_use":
                                tool_name = getattr(event, "name", "?")
                                _out(f"\n  ↳ [tool: {tool_name}]", flush=True)
                                print(f"       ↳ mcp tool: {tool_name}")
                            case "agent.mcp_tool_result":
                                print(f"       ↳ mcp tool result received")
                            case "agent.thinking":
                                print(f"       · thinking...")
                            case "session.status_idle":
                                print(f"       · session idle — done")
                                idle = True
                                break
                            case "session.status_running":
                                print(f"       · session running")
                            case "session.error" | "error":
                                _out(f"\n  ⚠ [error: {event}]", flush=True)
                                print(f"       ⚠ error: {event}")
                                idle = True
                                break
                            case _:
                                print(f"       · event: {event.type}")
                # stream closed — if not idle yet, wait briefly then reconnect
                print(f"       · stream closed (idle={idle})")
                if not idle:
                    print(f"       · reconnecting...")
                    time.sleep(1)
        except httpx.ReadTimeout:
            _out("\n  ⚠ [stream timeout — tool took >60s]\n\n", flush=True)
            print(f"       ⚠ stream read timeout")
        except Exception as exc:
            _out(f"\n  ⚠ [error: {exc}]\n\n", flush=True)
            print(f"       ⚠ exception: {exc}")
        else:
            _out("\n\n")
        print(f"[{_ts()}] ✓ done")

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    api_key = "abc"
    client  = anthropic.Anthropic(api_key=api_key)

    agent_id = get_or_create_agent(client)
    env_id   = get_or_create_environment(client)
    run_file_chat(client, agent_id, env_id)
