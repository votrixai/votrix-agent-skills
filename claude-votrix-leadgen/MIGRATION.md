# Migration Notes — Claude Code → Claude Managed Agents

This folder is a port of `votrix-leadgen/` (Claude Code skill pack) for the
Claude **Managed Agents API**. The original Claude Code version is untouched.

## What changed

### 1. Frontmatter cleanup
Each `SKILL.md` now uses only the fields Managed Agents understands:

```yaml
---
name: <skill-name>
description: <when to invoke, in one sentence>
---
```

Removed: `user-invocable`, `argument-hint`, `allowed-tools`. Tool access in
Managed Agents is controlled at the agent level (`tools` + `mcp_servers`),
not per-skill.

### 2. Skill descriptions rewritten
In Claude Code, skills are slash-invoked by the user. In Managed Agents,
the model chooses skills automatically based on the `description` field.
Every description was rewritten to answer *"when should the agent invoke
this skill?"* rather than *"what is this skill called?"*.

### 3. Slash-command references removed
References like `/apollo-prospector <campaign-dir>` were rewritten to
skill-name references like "hand off to the `apollo-prospector` skill".
Managed Agents skills don't call each other via slash commands.

### 4. Orchestrator skill removed
The `lead-gen/` orchestrator skill was deleted. Its logic lives in
`managed-agent.json` as the agent's **system prompt**. This is how
orchestration works in Managed Agents — the system prompt sequences
stages, the skills execute them.

### 5. Direct MCP servers
Three separate MCP servers are configured on the agent:

- **Apollo** — people search, organization search, contact enrichment
- **Tavily** — web search for market research and account deep dives
- **Firecrawl** — URL scraping for deep content extraction

Each is a remote HTTP MCP server referenced by URL in the agent config
and exposed via `mcp_toolset` entries in the `tools` array. Auth for
each server is supplied via **vaults** at session creation time (see
Anthropic's vault docs for `static_bearer` credentials).

### 6. Proxycurl removed
Proxycurl was dropped from the active configuration. The `account-deep-dive`
skill no longer references it. If you later want LinkedIn profile enrichment,
re-add it as a conditional step there.

### 7. Schemas bundled per skill
The six JSON schemas originally in `votrix-leadgen/config/schemas/` are now
distributed into each skill's `reference/` folder, so every skill travels
with its own schema when uploaded:

| Schema                         | Skill               |
|--------------------------------|---------------------|
| `business_context.schema.json` | `business-context`  |
| `icp_schema.schema.json`       | `icp-builder`       |
| `market_kb.schema.json`        | `market-intel`      |
| `lead_record.schema.json`      | `apollo-prospector` |
| `lead_score.schema.json`       | `lead-scorer`       |
| `campaign_intel.schema.json`   | `quality-gate`      |

Each SKILL.md references its schema as `reference/<name>.schema.json`, and
the agent can read it at runtime to validate outputs precisely rather than
relying on prose field lists.

### 8. Data operations upgraded
All skills now use **jq** for JSON file operations and **pandas** for
batch data processing and CSV export, instead of relying on the agent's
Read/Write tools for structured data. This provides:

- Precise JSON transformations (field mapping, merging, filtering)
- Proper CSV export with pandas (escaping, sorting, column selection)
- Vectorized scoring operations in lead-scorer
- Reliable deduplication and validation in quality-gate

### 9. State passing
The pipeline still uses JSON files in a campaign directory
(`output/<campaign>-<date>/*.json`) for stage-to-stage handoff. This works
because Managed Agents sessions have a working filesystem via the
`agent_toolset_20260401`. JSON operations are now performed via jq
through Bash rather than the Read/Write tools.

## Before you can run this

1. **Upload each skill** in `skills/` to your org as a custom skill. Each
   upload returns a `skill_*` ID. Replace the placeholder IDs in
   `managed-agent.json` with the real IDs.

2. **Configure MCP server URLs.** Replace the `REPLACE_WITH_*_MCP_URL`
   placeholders in `managed-agent.json` with the actual remote MCP
   server URLs for Apollo, Tavily, and Firecrawl.

3. **Set up vaults.** Create a vault in your Anthropic workspace and add
   a `static_bearer` credential for each MCP server, binding the API key
   to the exact MCP server URL. Pass `vault_ids` when creating sessions.

4. **Verify tool names.** Once the MCP servers are attached, inspect the
   list of tools each server exposes. If the real tool names differ from
   what the skills assume, update the relevant SKILL.md files. Currently
   the skills describe the *semantic* action (e.g. "Apollo people search")
   rather than hard-coding tool names — this was deliberate, so the model
   can match on intent.

5. **Create the agent** using `managed-agent.json` via the console or API.

## Known gaps / TODO

- **MCP server URLs.** You need hosted remote MCP endpoints for Apollo,
  Tavily, and Firecrawl that accept Bearer token auth. Replace the
  placeholder URLs in `managed-agent.json` with real endpoints.
- **Tool name verification.** The skills are written against semantic
  action names, not hard-coded MCP tool identifiers. First real run will
  tell you whether the agent picks the right tools; if not, pin tool
  names explicitly.
- **Cost tracking accuracy.** Credit counters in `pipeline_state.json`
  are incremented by the agent, not by the underlying vendor APIs. They
  reflect what the agent *thinks* it used, which may drift from real
  Apollo / Tavily / Firecrawl billing.
