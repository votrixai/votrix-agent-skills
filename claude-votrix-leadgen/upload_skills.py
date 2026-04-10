"""
Upload all leadgen skills and bind them to the managed agent.

Run once (after creating the agent with managed_agent.py):
    python claude-votrix-leadgen/upload_skills.py

What it does:
  1. Discovers every skill dir in skills/ (each has SKILL.md + optional reference/)
  2. Zips each skill into <skill-name>/<files> format
  3. Uploads via POST /v1/skills
  4. Caches skill IDs in .skill_ids.json
  5. PATCHes the agent to attach all skills
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import anthropic
import httpx

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

_DIR = Path(__file__).parent
_SKILLS_DIR = _DIR / "skills"
_SKILL_IDS_FILE = _DIR / ".skill_ids.json"
_AGENT_ID_FILE = _DIR / ".agent_id"

API_KEY = "REPLACE_WITH_ANTHROPIC_API_KEY"

HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "managed-agents-2026-04-01,skills-2025-10-02",
}

# ─────────────────────────────────────────────────────────────────────────────
# Upload helpers
# ─────────────────────────────────────────────────────────────────────────────


def _zip_skill(skill_dir: Path) -> bytes:
    """Pack SKILL.md + reference/ + examples/ into a zip with one top-level folder."""
    buf = io.BytesIO()
    folder = skill_dir.name
    with zipfile.ZipFile(buf, "w") as zf:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                arcname = f"{folder}/{path.relative_to(skill_dir)}"
                zf.writestr(arcname, path.read_bytes())
    buf.seek(0)
    return buf.read()


def upload_skill(skill_dir: Path, cached: dict[str, str]) -> str:
    """Upload a single skill, return skill_id. Uses cache to skip re-uploads."""
    name = skill_dir.name
    if name in cached:
        print(f"  [skip] {name} → {cached[name]} (cached)")
        return cached[name]

    zip_bytes = _zip_skill(skill_dir)

    with httpx.Client() as hclient:
        resp = hclient.post(
            "https://api.anthropic.com/v1/skills",
            headers=HEADERS,
            data={"display_title": name},
            files=[("files[]", ("skill.zip", zip_bytes, "application/zip"))],
            timeout=30,
        )
    if not resp.is_success:
        raise RuntimeError(f"Upload failed for {name} ({resp.status_code}): {resp.text}")

    body = resp.json()
    skill_id = body["id"]
    print(f"  [new]  {name} → {skill_id} (v{body.get('latest_version', '?')})")
    return skill_id


def upload_all_skills() -> dict[str, str]:
    """Upload every skill in skills/, return {name: skill_id} map."""
    cached = {}
    if _SKILL_IDS_FILE.exists():
        cached = json.loads(_SKILL_IDS_FILE.read_text())

    skill_dirs = sorted(d for d in _SKILLS_DIR.iterdir() if d.is_dir())
    print(f"Found {len(skill_dirs)} skills to upload:\n")

    result = {}
    for skill_dir in skill_dirs:
        result[skill_dir.name] = upload_skill(skill_dir, cached)

    _SKILL_IDS_FILE.write_text(json.dumps(result, indent=2))
    print(f"\nSkill IDs saved to {_SKILL_IDS_FILE.name}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Bind skills to agent
# ─────────────────────────────────────────────────────────────────────────────


def bind_skills_to_agent(client: anthropic.Anthropic, skill_ids: dict[str, str]) -> None:
    """PATCH the agent to include all skills."""
    if not _AGENT_ID_FILE.exists():
        print("\nNo .agent_id found — run managed_agent.py first to create the agent.")
        return

    agent_id = _AGENT_ID_FILE.read_text().strip()
    agent = client.beta.agents.retrieve(agent_id)

    existing = {s.skill_id for s in (agent.skills or [])}
    new_ids = set(skill_ids.values())

    if new_ids.issubset(existing):
        print(f"\n[agent] {agent_id} already has all {len(new_ids)} skills — nothing to do")
        return

    skills_payload = [
        {"type": "custom", "skill_id": sid, "version": "latest"}
        for sid in skill_ids.values()
    ]

    updated = client.beta.agents.update(
        agent_id,
        version=agent.version,
        skills=skills_payload,
    )
    print(f"\n[agent] {agent_id} updated to v{updated.version} with {len(updated.skills)} skill(s)")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = anthropic.Anthropic(api_key=API_KEY)
    skill_ids = upload_all_skills()
    bind_skills_to_agent(client, skill_ids)
    print("\nDone. Restart managed_agent.py to use the updated skills.")
