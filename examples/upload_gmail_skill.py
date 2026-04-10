"""
Upload the gmail-drafting skill and bind it to the votrix-gmail-agent.

Run once:
    python app/examples/upload_gmail_skill.py

What it does:
  1. Uploads SKILL.md + REFERENCE.md as a custom skill via POST /v1/skills
  2. Saves the returned skill_id to .gmail_skill_id
  3. Reads the current agent_id from .gmail_agent_id
  4. PATCHes the agent to add the skill (preserves existing tools/mcp_servers)
"""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import anthropic
import httpx

_DIR        = Path(__file__).parent
_SKILL_DIR  = Path(__file__).resolve().parent.parent.parent / "prompts" / "skills" / "gmail-drafting"
_SKILL_ID_FILE  = _DIR / ".gmail_skill_id"
_AGENT_ID_FILE  = _DIR / ".gmail_agent_id"

API_KEY = "abc"

def upload_skill(client: anthropic.Anthropic) -> str:
    """POST /v1/skills — zip SKILL.md + REFERENCE.md and upload, return skill_id.

    File format requirements (discovered via API probing):
      - Must be a ZIP file sent as files[] field
      - All files must be inside exactly ONE top-level folder inside the ZIP
      - SKILL.md must start with YAML frontmatter (---)

    Uses httpx directly: SDK 0.93 has a multipart bug that serialises file
    objects as their string repr, causing 400 errors.
    """
    if _SKILL_ID_FILE.exists():
        skill_id = _SKILL_ID_FILE.read_text().strip()
        print(f"[skill]  {skill_id} (cached — delete .gmail_skill_id to re-upload)")
        return skill_id

    # Pack files into a zip with a top-level folder
    buf = io.BytesIO()
    folder = _SKILL_DIR.name  # "gmail-drafting"
    with zipfile.ZipFile(buf, "w") as zf:
        for md_file in sorted(_SKILL_DIR.glob("*.md")):
            zf.writestr(f"{folder}/{md_file.name}", md_file.read_text())
    buf.seek(0)

    with httpx.Client() as hclient:
        resp = hclient.post(
            "https://api.anthropic.com/v1/skills",
            headers={
                "x-api-key":         API_KEY,
                "anthropic-version": "2023-06-01",
                "anthropic-beta":    "skills-2025-10-02",
            },
            data={"display_title": "Gmail Drafting Guide"},
            files=[("files[]", ("skill.zip", buf.read(), "application/zip"))],
            timeout=30,
        )
    if not resp.is_success:
        raise RuntimeError(f"Skill upload failed {resp.status_code}: {resp.text}")
    body = resp.json()

    skill_id = body["id"]
    _SKILL_ID_FILE.write_text(skill_id)
    print(f"[skill]  {skill_id} (created, version={body.get('latest_version')})")
    return skill_id


def bind_skill_to_agent(client: anthropic.Anthropic, skill_id: str) -> None:
    """PATCH /v1/agents/{id} — add skill to agent's skills list."""
    if not _AGENT_ID_FILE.exists():
        sys.exit("No .gmail_agent_id found — run gmail_managed_agent.py first to create the agent.")

    agent_id = _AGENT_ID_FILE.read_text().strip()
    agent    = client.beta.agents.retrieve(agent_id)

    # Build the updated skills list (avoid duplicates)
    existing_ids = {s.skill_id for s in (agent.skills or [])}
    if skill_id in existing_ids:
        print(f"[agent]  {agent_id} already has skill {skill_id} — nothing to do")
        return

    new_skills = [
        {"type": s.type, "skill_id": s.skill_id, **({"version": s.version} if s.version else {})}
        for s in (agent.skills or [])
    ] + [{"type": "custom", "skill_id": skill_id, "version": "latest"}]

    updated = client.beta.agents.update(
        agent_id,
        version=agent.version,
        skills=new_skills,
    )
    print(f"[agent]  {agent_id} updated to v{updated.version} with {len(updated.skills)} skill(s)")


if __name__ == "__main__":
    client   = anthropic.Anthropic(api_key=API_KEY)
    skill_id = upload_skill(client)
    bind_skill_to_agent(client, skill_id)
    print("\nDone. Restart gmail_managed_agent.py to use the new skill.")
