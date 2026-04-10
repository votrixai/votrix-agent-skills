---
name: icp-builder
description: Build the Ideal Customer Profile (ICP) that drives targeting for the rest of the lead gen pipeline. Invoke this after business-context is complete, to define company scale, industries, personas, and targeting criteria.
---

# ICP Builder

Builds the Ideal Customer Profile (ICP) that drives targeting for the rest of the pipeline. Critically, this is where `company_scale` is set — it determines which downstream stages run and how scoring works.

## Prerequisites

- `business_context.json` must exist in the campaign directory (produced by the `business-context` skill).

## Process

1. **Load business context.** Use jq to read `business_context.json`:
   ```bash
   jq '.' "$CAMPAIGN_DIR/business_context.json"
   ```

2. **Determine company scale** (critical — this drives the entire pipeline):
   - **SMB** (1–200 employees): pass/fail scoring, basic intel, Apollo-only
   - **Mid-Market** (200–2000 employees): 3D scoring, account research, Tavily+Firecrawl
   - **Enterprise** (2000+ employees): 4D scoring, full enrichment

3. **Gather ICP criteria** from the user:
   - **Industries** — which to target (suggest based on business_context)
   - **Employee range** — min / max employee count
   - **Revenue range** — min / max revenue (optional)
   - **Personas** — for each persona: title patterns, seniority levels, departments
   - **Geography** — countries and regions
   - **Technologies** — tech stack filters (optional)
   - **Exclusions** — companies, domains, or industries to exclude
   - **Lead volume target** — how many qualified leads to produce (apply defaults from `reference/scale_defaults.json`)

4. **Apply scale defaults.** Load `reference/scale_defaults.json` and suggest defaults based on `company_scale`. The user may override.

5. **Validate and confirm.** Show the complete ICP summary and ask for confirmation before saving.

6. **Save outputs** using jq:
   ```bash
   # Write ICP schema
   echo "$ICP_JSON" | jq '.' > "$CAMPAIGN_DIR/icp_schema.json"
   
   # Update pipeline state
   jq --arg scale "$COMPANY_SCALE" '.company_scale = $scale | .completed_steps += [1] | .current_step = 1' \
     "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
   ```

7. **Report and hand off.** Tell the user which branch of the pipeline will run based on `company_scale`, and hand off to the next stage:
   - SMB → skip market-intel, go straight to `apollo-prospector`
   - Mid / Enterprise → `market-intel` next

## Schema

Output must conform to `reference/icp_schema.schema.json` (bundled with this skill).

## Scale Defaults

See `reference/scale_defaults.json`.

## Examples

See `examples/` for ICPs at each scale tier.
