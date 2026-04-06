# Votrix LeadGen — Architecture

## Overview

Votrix LeadGen is a multi-skill Claude Code pipeline for B2B lead generation. It chains 8 skills (Skill 0–7) plus a meta-orchestrator to produce a scored CSV of decision-makers ready for cold outreach, along with campaign intelligence JSON.

## Design Principles

1. **Skill-based modularity** — Each skill is independently invocable and testable
2. **JSON state passing** — All inter-skill state flows via JSON files in the output directory
3. **Scale-aware behavior** — SMB/Mid/Enterprise paths differ in scoring depth, intel richness, and API usage
4. **Human-in-the-loop** — Calibration checkpoint (Skill 3.5) before committing API credits
5. **Cost transparency** — Credit usage tracked throughout the pipeline

## Skill Chain

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐
│  0. Business     │───▶│  1. ICP      │───▶│  2. Market   │
│     Context      │    │     Builder   │    │     Intel    │
└─────────────────┘    └──────────────┘    └──────┬───────┘
                                                   │
                        ┌──────────────┐           │
                        │  3. Apollo   │◀──────────┘
                        │     Prospector│
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  3.5 Human   │
                        │  Calibration │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  4. Lead     │
                        │     Scorer   │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  5. Account  │  (Mid/Enterprise only)
                        │  Deep Dive   │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  6. Lead     │
                        │     Intel    │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  7. Quality  │──▶ leads.csv
                        │     Gate     │──▶ campaign_intel.json
                        └──────────────┘──▶ campaign_summary.txt
```

## State Flow

All state passes via JSON files in `output/<campaign-name>-<YYYY-MM-DD>/`:

| File | Producer | Consumer |
|------|----------|----------|
| `business_context.json` | Skill 0 | Skills 1, 2, 4, 6 |
| `icp_schema.json` | Skill 1 | Skills 2, 3, 4, 7 |
| `market_kb.json` | Skill 2 | Skills 4, 5, 6 |
| `apollo_query_params.json` | Skill 3 | — (audit trail) |
| `calibration_leads.json` | Skill 3 | Skill 3.5 |
| `calibration_feedback.json` | Skill 3.5 | Skill 3 |
| `raw_leads.json` | Skill 3 | Skill 4 |
| `scored_leads.json` | Skill 4 | Skills 5, 6, 7 |
| `enriched_leads.json` | Skill 5 | Skill 6 |
| `intel_leads.json` | Skill 6 | Skill 7 |
| `leads.csv` | Skill 7 | End user |
| `campaign_intel.json` | Skill 7 | End user |
| `campaign_summary.txt` | Skill 7 | End user |
| `pipeline_state.json` | All skills | Orchestrator |

## Company Scale Modes

### SMB (`company_scale: "smb"`)
- **Scoring**: Pass/fail binary (Skill 4)
- **Intel**: Pain signal as question format (Skill 6, Haiku)
- **Deep Dive**: Skipped (Skill 5)
- **CSV columns**: Core fields + pass/fail + pain_signal
- **API cost**: Lowest — Apollo only, no Tavily/Proxycurl per-lead

### Mid-Market (`company_scale: "mid"`)
- **Scoring**: 3D — Fit, Intent, Timing (Skill 4)
- **Intel**: lead_intel + email_subject + email_opening (Skill 6)
- **Deep Dive**: Tavily + Firecrawl for A/B tier leads (Skill 5)
- **CSV columns**: Core + 3D scores + intel fields
- **API cost**: Moderate — Tavily/Firecrawl for top leads

### Enterprise (`company_scale: "enterprise"`)
- **Scoring**: 4D — Fit, Intent, Timing, Authority with confidence (Skill 4)
- **Intel**: Full suite + trigger_detail + email_cta (Skill 6)
- **Deep Dive**: Tavily + Firecrawl + Proxycurl for A/B leads (Skill 5)
- **CSV columns**: All fields
- **API cost**: Highest — full enrichment stack

## External API Integration

APIs are integrated via MCP (Model Context Protocol) servers configured in `.claude/settings.json`. This eliminates shell scripts — Claude calls MCP tools directly and uses Read/Write for all JSON I/O.

| API | MCP Server | Purpose | Used By | Credits/Cost |
|-----|------------|---------|---------|--------------|
| Apollo.io | `composio` | Lead search & contact data | Skill 3 | ~1 credit/lead |
| Tavily | `tavily` | Web search for market intel & account research | Skills 2, 5 | ~1 credit/search |
| Firecrawl | `firecrawl` | Web page scraping for deep research | Skills 2, 5 | ~1 credit/page |
| Proxycurl | `proxycurl` | LinkedIn profile enrichment | Skill 5 (Enterprise) | ~1 credit/profile |

All APIs are accessed via MCP — no Bash or shell scripts in the pipeline.

## Data Handling

- **Reading state**: Skills use Read to load JSON files from the campaign directory
- **Writing state**: Skills use Write to save JSON/CSV output
- **No shell scripts**: JSON transformation is done by Claude's reasoning, not `jq`
- **No intermediate files**: API responses are processed inline and written directly to output

## Pipeline State Tracking

`pipeline_state.json` tracks:
- Current step and completion status
- Company scale mode
- Credit usage per API
- Timestamps for each skill execution
- Error log for any failed steps

## Directory Structure

```
votrix-leadgen/
├── .claude/skills/          # Skill definitions
├── config/schemas/          # JSON Schema contracts
├── output/                  # Campaign output directories
├── .env.example             # API key template
├── ARCHITECTURE.md          # This file
└── README.md                # Usage guide
```

## Error Handling

- MCP servers validate API keys at startup — missing keys surface immediately
- Composio handles Apollo authentication via its managed connection
- Skills validate input JSON against schemas before processing
- The orchestrator can resume from the last successful step via `pipeline_state.json`
