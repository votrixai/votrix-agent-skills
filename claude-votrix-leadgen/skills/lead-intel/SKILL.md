---
name: lead-intel
description: Generate personalized outreach intelligence for each qualified lead — pain signals, lead insights, email subjects and openings, and (for enterprise) trigger details and CTAs. Output depth scales by company_scale. Invoke after lead-scorer (and account-deep-dive for mid/enterprise).
---

# Lead Intel

Generates personalized outreach intelligence for each qualified lead. Output depth varies by `company_scale`.

## Prerequisites

- `scored_leads.json` must exist in the campaign directory.
- `business_context.json` must exist in the campaign directory.
- `icp_schema.json` must exist in the campaign directory.
- `enriched_leads.json` (optional, Mid / Enterprise — from `account-deep-dive`)
- `market_kb.json` (optional — enhances intel quality)
- `pipeline_state.json` must exist with `company_scale` set.

## Intel Modes

### SMB

For each **passing** lead, generate:
- **`pain_signal`** — a question-format hook that surfaces a likely pain point
  - Format: *"Are you still [doing painful thing] when you could [better outcome]?"*
  - Specific to their role and industry
  - Keep it tight — this is a cost-efficient mode

**Input:** `scored_leads.json` (pass verdicts only)
**Batch:** process all passing leads at once

### Mid-Market

For each **A and B tier** lead, generate:
- **`pain_signal`** — detailed pain hypothesis (statement, not question)
- **`lead_intel`** — 2–3 sentence personalized insight connecting their situation to the solution
- **`email_subject`** — suggested subject line (<60 chars, no clickbait)
- **`email_opening`** — first 1–2 sentences of a personalized cold email

**Input:** `enriched_leads.json` if available, otherwise `scored_leads.json`
**Batch:** A-tier first, then B-tier

### Enterprise

For each **A and B tier** lead, everything from Mid-Market **plus**:
- **`trigger_detail`** — specific trigger event driving outreach timing (from account research)
- **`email_cta`** — tailored call-to-action based on authority level and likely priorities

**Input:** `enriched_leads.json` (should be available for A/B leads)
**Batch:** process individually for maximum personalization

## Data Operations

Use **jq** for filtering and merging, **pandas** for batch intel generation:

```bash
# Filter qualified leads (SMB)
jq '[.[] | select(.score.verdict == "pass")]' "$CAMPAIGN_DIR/scored_leads.json"

# Filter qualified leads (Mid/Enterprise)
jq '[.[] | select(.score.verdict == "A" or .score.verdict == "B")]' "$CAMPAIGN_DIR/enriched_leads.json"

# Merge intel fields into lead records
jq --argjson intel "$INTEL_ARRAY" '
  [range(length)] | map(. as $i | input[$i] + $intel[$i])
' "$CAMPAIGN_DIR/scored_leads.json" > "$CAMPAIGN_DIR/intel_leads.json"
```

```python
import pandas as pd, json

# Load leads into DataFrame for batch processing
with open(f"{campaign_dir}/scored_leads.json") as f:
    df = pd.DataFrame(json.load(f))

# Filter by verdict
qualified = df[df["verdict"].isin(["A", "B"])].copy()

# Add intel columns (populated by the LLM per-lead)
qualified["pain_signal"] = ""
qualified["lead_intel"] = ""
qualified["email_subject"] = ""
qualified["email_opening"] = ""

# Save
qualified.to_json(f"{campaign_dir}/intel_leads.json", orient="records", indent=2)
```

## Process

1. **Load inputs.** Use jq to read scored/enriched leads, business context, ICP, and market KB.

2. **Filter leads.** Use jq to select only leads meeting the mode's criteria:
   - SMB: `jq '[.[] | select(.score.verdict == "pass")]'`
   - Mid / Enterprise: `jq '[.[] | select(.score.verdict == "A" or .score.verdict == "B")]'`

3. **Generate intel.** For each qualified lead, use the business context and any available enrichment data to generate personalized outreach content.

4. **Apply templates.** Reference `reference/intel_templates.md` for tone, format, and quality guidelines.

5. **Save output.** Use jq or pandas to write `intel_leads.json` — each entry is the lead record merged with intel fields.

6. **Report summary.** Use jq or pandas to count leads with intel generated and display sample of best pieces.

7. **Update pipeline state.** Use jq to mark step 6 complete:
   ```bash
   jq '.completed_steps += [6] | .current_step = 6' \
     "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
   ```

8. **Hand off** to `quality-gate`.

## Intel Templates

See `reference/intel_templates.md` for guidelines on tone, format, and quality.
