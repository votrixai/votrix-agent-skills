"""
Votrix LeadGen Managed Agent — file-based conversation mode.

How to use:
  Terminal 1:  python claude-votrix-leadgen/managed_agent.py
  Editor:      open input.txt  → type a message → save
  Terminal 2:  tail -f output.txt   (or just open the file)

Flow:
  1. Script watches input.txt (polls every 0.3 s for mtime change).
  2. On save: reads message, clears input.txt, streams reply into output.txt.
  3. Session stays alive → full conversation context across turns.
  4. Write 'quit' in input.txt to stop.

MCP server (via Composio):
  Single Composio MCP endpoint that routes to Apollo, Tavily, and Firecrawl tools.

SDK calls:
  client.beta.agents.create()
  client.beta.environments.create()
  client.beta.sessions.create(agent=..., environment_id=..., vault_ids=[...])
  client.beta.sessions.events.stream(session_id)
  client.beta.sessions.events.send(session_id, events=[...])
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import httpx

# ─────────────────────────────────────────────────────────────────────────────
# Config — replace these before running
# ─────────────────────────────────────────────────────────────────────────────

API_KEY = "REPLACE_WITH_ANTHROPIC_API_KEY"
# Composio MCP URL — single endpoint that routes to Apollo, Tavily, Firecrawl via meta-tools
COMPOSIO_MCP_URL = (
    "https://backend.composio.dev/v3/mcp"
    "/002a0b5e-dedf-4d93-8488-d48733764d3e"
    "/mcp?user_id=pg-test-a4a86337-48ea-4e6b-8367-17fa28d65c51"
    "&api_key=ak_8vG7x_RyPvOyIXeHUSDR"
)

# ─────────────────────────────────────────────────────────────────────────────
# File paths
# ─────────────────────────────────────────────────────────────────────────────

_DIR = Path(__file__).parent

INPUT_FILE = _DIR / "input.txt"
OUTPUT_FILE = _DIR / "output.txt"

_AGENT_ID_FILE = _DIR / ".agent_id"
_ENV_ID_FILE = _DIR / ".env_id"

# ─────────────────────────────────────────────────────────────────────────────
# Agent config
# ─────────────────────────────────────────────────────────────────────────────

_STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

SYSTEM_PROMPT = """\
You are the orchestrator for the Votrix B2B lead generation pipeline. Your job is to \
run a structured, multi-stage campaign end to end, invoking the right skill at each \
stage, passing state forward via files in the campaign directory, and never skipping \
the human calibration gate.

## Pipeline stages (run in order)

0. business-context — always first if no business_context.json exists yet.
   Produces business_context.json and initializes pipeline_state.json. Establishes
   the campaign_dir (output/<campaign-name>-<YYYY-MM-DD>/).

1. icp-builder — produces icp_schema.json and sets company_scale in pipeline_state.
   company_scale determines which stages run next:
     - "smb"        → skip market-intel, skip account-deep-dive
     - "mid"        → run everything
     - "enterprise" → run everything

2. market-intel — SKIP for SMB. For mid/enterprise, produces market_kb.json using
   Tavily search and Firecrawl scraping via Composio.

3. apollo-prospector (phase 1, calibration) — produces calibration_leads.json
   (typically ~50 leads) via Apollo through Composio.

3.5. human-calibration — BLOCKING. Show sample leads, collect feedback, produce
   calibration_feedback.json. DO NOT proceed until approved_for_bulk_pull is true.
   If the user rejects, hand back to icp-builder to adjust, then re-run phase 1.

4. apollo-prospector (phase 2, bulk pull) — reads calibration_feedback.json and
   produces raw_leads.json.

5. lead-scorer — scores leads per company_scale. Produces scored_leads.json.

6. account-deep-dive — SKIP for SMB. For mid/enterprise, enriches A and B leads
   with Tavily + Firecrawl research via Composio. Produces enriched_leads.json.

7. lead-intel — generates per-lead outreach intelligence. Produces intel_leads.json.

8. quality-gate — validates, exports leads.csv, produces campaign_intel.json and
   campaign_summary.txt. This is the final stage.

## Data handling

Use jq for all JSON file operations (reading, writing, merging, filtering). Use \
pandas (via python3) for CSV export, batch data analysis, and scoring operations. \
Do not rely on the Read/Write tools for structured data — use Bash with jq and \
python3 instead, as they provide precise control over data transformations.

## Rules

- State is passed between stages via JSON files in the campaign directory. Always
  read the latest pipeline_state.json before invoking a stage.
- Never proceed past human-calibration without an explicit "approved" signal from
  the user in calibration_feedback.json.
- Track credit usage (Apollo, Tavily, Firecrawl) in pipeline_state.json as you go.
- Before starting a new campaign, look for existing incomplete campaigns in output/
  and offer to resume.
- Before beginning, estimate API costs based on company_scale and lead_volume_target
  and confirm with the user.

## Cost estimates (rough)

| Scale      | Apollo       | Tavily         | Firecrawl      |
|------------|--------------|----------------|----------------|
| SMB (100)  | ~100 credits | 0              | 0              |
| Mid (75)   | ~75 credits  | ~30 searches   | ~10 scrapes    |
| Ent (50)   | ~50 credits  | ~40 searches   | ~15 scrapes    |
"""

AGENT_CONFIG = {
    "name": "votrix-leadgen-agent",
    "model": "claude-sonnet-4-6",
    "system": SYSTEM_PROMPT,
    "mcp_servers": [
        {"type": "url", "name": "composio", "url": COMPOSIO_MCP_URL},
    ],
    "tools": [
        {
            "type": "agent_toolset_20260401",
            "default_config": {
                "permission_policy": {"type": "always_allow"},
            },
        },
        {
            "type": "mcp_toolset",
            "mcp_server_name": "composio",
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
    """Append text to output.txt."""
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
        name="votrix-leadgen-env",
        config={"type": "cloud"},
    )
    _ENV_ID_FILE.write_text(env.id)
    print(f"[env]   {env.id} (created)")
    return env.id


# ─────────────────────────────────────────────────────────────────────────────
# File-based conversation loop
# ─────────────────────────────────────────────────────────────────────────────


def run_file_chat(client: anthropic.Anthropic, agent_id: str, env_id: str) -> None:
    INPUT_FILE.touch()
    INPUT_FILE.write_text("")

    session = client.beta.sessions.create(agent=agent_id, environment_id=env_id)

    _out(f"{'─' * 60}\n")
    _out(f"Session {session.id}  started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    _out(f"Write your message in input.txt and save to send.\n")
    _out(f"{'─' * 60}\n\n")

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

        if user_input.lower() in ("quit", "exit", "q"):
            print("[bye]")
            _out("\n[session ended]\n")
            break

        INPUT_FILE.write_text("")
        last_mtime = INPUT_FILE.stat().st_mtime

        _out(f"[{_ts()}] You: {user_input}\n\n")
        _out(f"[{_ts()}] Agent: ", flush=True)
        print(f"[{_ts()}] → processing...")

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
                print(f"       · stream closed (idle={idle})")
                if not idle:
                    print(f"       · reconnecting...")
                    time.sleep(1)
        except httpx.ReadTimeout:
            _out("\n  ⚠ [stream timeout — tool took too long]\n\n", flush=True)
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
    client = anthropic.Anthropic(api_key=API_KEY)
    agent_id = get_or_create_agent(client)
    env_id = get_or_create_environment(client)
    run_file_chat(client, agent_id, env_id)
