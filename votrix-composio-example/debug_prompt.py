"""
Debug script — reveals the complete runtime context of the Gmail managed agent.

Two-phase approach:
  Phase 1: retrieve stored agent config from Anthropic API (what YOU configured)
  Phase 2: start a session and ask the agent to dump all its files + instructions
            (reveals what Anthropic injected: skills, tool descriptions, env context)

Run:
  python app/examples/debug_prompt.py
Output is printed to stdout AND written to debug_prompt_output.txt
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import anthropic
import httpx

_DIR = Path(__file__).parent
_AGENT_ID_FILE = _DIR / ".gmail_agent_id"
_ENV_ID_FILE   = _DIR / ".gmail_env_id"
OUTPUT_FILE    = _DIR / "debug_prompt_output.txt"

COMPOSIO_API_KEY = "abc"
COMPOSIO_GMAIL_MCP_URL = (
    "https://backend.composio.dev/v3/mcp"
    "/5a629a28-ec72-4601-b192-cf705ecc6d01"
    f"/mcp?user_id=votrix-claude-managed-agent-test&api_key={COMPOSIO_API_KEY}"
)

_STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

# ── The introspection prompt ──────────────────────────────────────────────────
# Asks the agent to reveal everything it can see about its own context.
# We send multiple targeted messages in sequence within the same session
MESSAGES = [
    "Run this bash command and paste the COMPLETE raw stdout, do not truncate or summarize:\n\ncat /workspace/skills/gmail-drafting/SKILL.md",
    "Run this bash command and paste the COMPLETE raw stdout, do not truncate or summarize:\n\ncat /workspace/skills/gmail-drafting/REFERENCE.md",
    "Run this bash command and paste the COMPLETE raw stdout, do not truncate or summarize:\n\nfind /workspace -type f | sort; echo '---'; env | sort",
]


def tee(text: str, f) -> None:
    """Print to stdout and write to file simultaneously."""
    print(text, end="", flush=True)
    f.write(text)
    f.flush()


def phase1_retrieve_config(client: anthropic.Anthropic, f) -> None:
    tee("\n" + "═" * 70 + "\n", f)
    tee("PHASE 1 — STORED AGENT CONFIG (what you configured via API)\n", f)
    tee("═" * 70 + "\n\n", f)

    if not _AGENT_ID_FILE.exists():
        tee("No cached agent ID found. Run gmail_managed_agent.py first.\n", f)
        return

    agent_id = _AGENT_ID_FILE.read_text().strip()
    tee(f"Agent ID: {agent_id}\n\n", f)

    try:
        agent = client.beta.agents.retrieve(agent_id)
        tee(f"Name:    {agent.name}\n", f)
        tee(f"Model:   {agent.model}\n", f)
        tee(f"Version: {agent.version}\n\n", f)
        tee("── system field ──\n", f)
        tee(agent.system + "\n\n", f)
        tee("── mcp_servers ──\n", f)
        for s in (agent.mcp_servers or []):
            tee(f"  {s}\n", f)
        tee("\n── tools ──\n", f)
        for t in (agent.tools or []):
            tee(f"  {t}\n", f)
    except Exception as e:
        tee(f"Error retrieving agent: {e}\n", f)


def send_and_wait(client: anthropic.Anthropic, session_id: str, user_text: str, f) -> None:
    """Send one message to the session and stream until idle."""
    idle = False
    first = True
    try:
        while not idle:
            with client.beta.sessions.events.stream(
                session_id, timeout=_STREAM_TIMEOUT
            ) as stream:
                if first:
                    client.beta.sessions.events.send(
                        session_id,
                        events=[{
                            "type": "user.message",
                            "content": [{"type": "text", "text": user_text}],
                        }],
                    )
                    first = False
                for event in stream:
                    match event.type:
                        case "agent.message":
                            for block in event.content:
                                if block.type == "text":
                                    tee(block.text, f)
                        case "agent.mcp_tool_use":
                            tool_name = getattr(event, "name", "?")
                            tee(f"\n  [tool: {tool_name}]\n", f)
                        case "agent.thinking":
                            pass
                        case "session.status_idle":
                            idle = True
                            break
                        case "session.error" | "error":
                            tee(f"\n[ERROR: {event}]\n", f)
                            idle = True
                            break
            if not idle:
                time.sleep(1)
    except httpx.ReadTimeout:
        tee("\n[stream timeout after 120s]\n", f)
    except Exception as e:
        tee(f"\n[exception: {e}]\n", f)


def phase2_introspect_session(client: anthropic.Anthropic, f) -> None:
    tee("\n" + "═" * 70 + "\n", f)
    tee("PHASE 2 — LIVE SESSION INTROSPECTION\n", f)
    tee("═" * 70 + "\n\n", f)

    if not _AGENT_ID_FILE.exists() or not _ENV_ID_FILE.exists():
        tee("Missing agent/env ID files. Run gmail_managed_agent.py first.\n", f)
        return

    agent_id = _AGENT_ID_FILE.read_text().strip()
    env_id   = _ENV_ID_FILE.read_text().strip()

    tee(f"Creating session (agent={agent_id}, env={env_id})...\n\n", f)
    session = client.beta.sessions.create(agent=agent_id, environment_id=env_id)
    tee(f"Session: {session.id}\n\n", f)

    for i, msg in enumerate(MESSAGES, 1):
        tee(f"── Request {i}: {msg[:60]}... ──\n\n", f)
        send_and_wait(client, session.id, msg, f)
        tee("\n\n", f)

    tee("═" * 70 + "\n", f)
    tee("Done. Full output saved to: debug_prompt_output.txt\n", f)


if __name__ == "__main__":
    api_key = "abc"
    client = anthropic.Anthropic(api_key=api_key)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        phase1_retrieve_config(client, f)
        phase2_introspect_session(client, f)
