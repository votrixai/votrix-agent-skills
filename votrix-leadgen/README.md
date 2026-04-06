# Votrix LeadGen

B2B lead generation pipeline built as a Claude Code skill system. Chains 8 skills to produce scored, enriched leads ready for cold outreach.

## Quick Start

1. **Copy environment file** and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

2. **Run the full pipeline** (recommended):
   ```
   /lead-gen
   ```
   The orchestrator will walk you through each step interactively.

3. **Or run individual skills:**
   ```
   /business-context        # Set up your business profile
   /icp-builder             # Define your ideal customer profile
   /market-intel            # Research market & competitors
   /apollo-prospector       # Pull leads from Apollo
   /human-calibration       # Review sample leads & calibrate
   /lead-scorer             # Score leads by fit
   /account-deep-dive       # Deep research on top accounts
   /lead-intel              # Generate outreach intelligence
   /quality-gate            # Validate & export CSV
   ```

## Output

Each campaign generates a directory: `output/<campaign-name>-<YYYY-MM-DD>/`

Key outputs:
- **`leads.csv`** — Scored leads ready for import into your outreach tool
- **`campaign_intel.json`** — Full intelligence payload per lead
- **`campaign_summary.txt`** — Human-readable campaign summary

## Company Scale Modes

| Mode | Scoring | Intel Depth | APIs Used |
|------|---------|-------------|-----------|
| **SMB** | Pass/Fail | Pain signal (question) | Apollo |
| **Mid-Market** | 3D (Fit/Intent/Timing) | Lead intel + email draft | Apollo, Tavily, Firecrawl |
| **Enterprise** | 4D (+ Authority) | Full suite + triggers | Apollo, Tavily, Firecrawl, Proxycurl |

## Required API Keys

| Key | Required For | Get It |
|-----|-------------|--------|
| `COMPOSIO_API_KEY` | All modes (Apollo via Composio) | [composio.dev](https://composio.dev/) |
| `TAVILY_API_KEY` | Mid + Enterprise | [tavily.com](https://tavily.com/) |
| `FIRECRAWL_API_KEY` | Mid + Enterprise | [firecrawl.dev](https://firecrawl.dev/) |
| `PROXYCURL_API_KEY` | Enterprise only | [proxycurl.com](https://proxycurl.com/) |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design, state flow, and skill chain diagram.

## Testing the Pipeline

### End-to-End Test (SMB)

1. Run `/business-context` — provide your company info
2. Run `/icp-builder` — select SMB scale, define target personas
3. Run `/apollo-prospector` — pull ~50 calibration leads
4. Run `/human-calibration` — review 5 samples, provide feedback
5. Apollo pulls remaining leads based on calibration
6. Run `/lead-scorer` — pass/fail scoring
7. Run `/lead-intel` — generate pain signals
8. Run `/quality-gate` — validate and export

Check `output/` for your campaign directory with `leads.csv`.

### Resuming a Pipeline

The orchestrator tracks progress in `pipeline_state.json`. If interrupted, run `/lead-gen` again and it will offer to resume from the last completed step.
