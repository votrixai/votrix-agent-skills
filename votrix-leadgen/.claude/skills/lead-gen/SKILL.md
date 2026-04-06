---
name: lead-gen
description: Full B2B lead generation pipeline — chains all skills from business context through CSV export
user-invocable: true
argument-hint: "[campaign-name]"
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
  - WebSearch
  - WebFetch
  - Skill
  - mcp__tavily__search
  - mcp__firecrawl__scrape
  - mcp__proxycurl__lookup
---

# Lead Gen Pipeline Orchestrator

Meta-skill that chains all lead generation skills (0-7) into a complete pipeline run. Handles branching based on company_scale, resume from interruption, and cost tracking.

## Overview

This orchestrator runs the full pipeline:

```
Business Context → ICP Builder → Market Intel → Apollo Prospector
→ Human Calibration → (Bulk Pull) → Lead Scorer
→ Account Deep Dive → Lead Intel → Quality Gate → CSV Export
```

## Process

### 1. Check for Existing Campaign

Look for `pipeline_state.json` in recent output directories:
- If found with incomplete steps, ask: "Resume campaign '{name}' from step {N}?"
- If user says yes, resume from last completed step
- If no, start fresh

### 2. Run Skills in Order

#### Step 0: Business Context
- Invoke `/business-context` (or `/business-context <campaign-name>` if provided)
- Wait for completion → `business_context.json` created

#### Step 1: ICP Builder
- Invoke `/icp-builder <campaign-dir>`
- Wait for completion → `icp_schema.json` created
- **Critical**: `company_scale` is now set — determines pipeline branching

#### Step 2: Market Intelligence (Mid/Enterprise only)
- If `company_scale` is "mid" or "enterprise":
  - Invoke `/market-intel <campaign-dir>`
  - Wait for completion → `market_kb.json` created
- If SMB: Skip, inform user

#### Step 3: Apollo Prospector (Calibration)
- Invoke `/apollo-prospector <campaign-dir>`
- Wait for completion → `calibration_leads.json` created

#### Step 3.5: Human Calibration
- Invoke `/human-calibration <campaign-dir>`
- Wait for completion → `calibration_feedback.json` created
- **This is a blocking checkpoint** — user must approve before continuing

#### Step 3 (continued): Apollo Prospector (Bulk Pull)
- Invoke `/apollo-prospector <campaign-dir>` again
- Apollo reads `calibration_feedback.json` and does bulk pull
- Wait for completion → `raw_leads.json` created

#### Step 4: Lead Scorer
- Invoke `/lead-scorer <campaign-dir>`
- Wait for completion → `scored_leads.json` created
- Report score distribution to user

#### Step 5: Account Deep Dive (Mid/Enterprise, A/B leads only)
- If `company_scale` is "mid" or "enterprise":
  - Invoke `/account-deep-dive <campaign-dir>`
  - Wait for completion → `enriched_leads.json` created
- If SMB: Skip

#### Step 6: Lead Intel
- Invoke `/lead-intel <campaign-dir>`
- Wait for completion → `intel_leads.json` created

#### Step 7: Quality Gate & Export
- Invoke `/quality-gate <campaign-dir>`
- Wait for completion → `leads.csv` + `campaign_intel.json` + `campaign_summary.txt`

### 3. Final Report

Present the campaign summary:
- Total leads found → scored → qualified → exported
- Score distribution (pass/fail or A/B/C breakdown)
- API credit usage summary
- File locations for all outputs
- Recommended next steps

## Cost Estimation

Before starting, estimate API costs based on `company_scale` and `lead_volume_target`:

| Scale | Apollo | Tavily | Firecrawl | Proxycurl | Est. Total |
|-------|--------|--------|-----------|-----------|------------|
| SMB (100 leads) | ~100 credits | 0 | 0 | 0 | ~100 credits |
| Mid (75 leads) | ~75 credits | ~30 searches | ~10 scrapes | 0 | ~115 credits |
| Enterprise (50 leads) | ~50 credits | ~40 searches | ~15 scrapes | ~15 lookups | ~120 credits |

Show this estimate to the user and confirm before proceeding.

## Error Handling

- If any skill fails, save the error to `pipeline_state.json` and inform the user
- Offer to retry the failed step or skip it (where safe)
- Never proceed past Human Calibration without explicit approval
- Track all API costs even if a step fails

## Resume Logic

When resuming from `pipeline_state.json`:
1. Read `completed_steps` array
2. Identify the next incomplete step
3. Verify all prerequisite files exist for that step
4. If prerequisites missing, re-run the producing step first
5. Continue the pipeline from there
