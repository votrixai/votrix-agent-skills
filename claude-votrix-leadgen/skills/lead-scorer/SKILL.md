---
name: lead-scorer
description: Score leads against the ICP. Mode is determined by company_scale — SMB is pass/fail, Mid-Market is 3D scoring, Enterprise is 4D scoring with confidence. Invoke after apollo-prospector bulk pull produces raw_leads.json.
---

# Lead Scorer

Scores each lead against the ICP. Scoring mode is determined by `company_scale` in `pipeline_state.json`.

## Prerequisites

- `raw_leads.json` must exist in the campaign directory.
- `icp_schema.json` must exist in the campaign directory.
- `pipeline_state.json` must exist with `company_scale` set.
- `market_kb.json` (optional, Mid / Enterprise) — enhances scoring if available.

## Scoring Modes

### SMB — Pass / Fail (`company_scale: "smb"`)

Binary scoring: does this lead match the ICP or not?

**Criteria** (see `reference/scoring_rubric_smb.md`):
- Title matches persona patterns — required
- Company size within range — required
- Industry matches — required
- Geography matches — required
- Email verified or guessed — preferred but not required

**Verdict:** `pass` or `fail` with `rejection_reason`.
**Batch size:** 50 leads per scoring pass.

### Mid-Market — 3D Scoring (`company_scale: "mid"`)

Three-dimensional scoring on a 0–100 scale:

1. **Fit** (40% weight): title match, company size, industry, technology overlap
2. **Intent** (35% weight): recent activity signals, hiring patterns, tech changes
3. **Timing** (25% weight): funding events, leadership changes, expansion signals

**Verdict:** A (≥75), B (50–74), C (<50).
**Batch size:** 30 leads per scoring pass.

### Enterprise — 4D Scoring (`company_scale: "enterprise"`)

Four-dimensional scoring with per-dimension confidence scores:

1. **Fit** (30%): Mid + organizational complexity match
2. **Intent** (25%): Mid + strategic initiative alignment
3. **Timing** (25%): Mid + budget cycle indicators
4. **Authority** (20%): decision-making power, org-chart position, buying-committee role

Each dimension includes a `confidence` score (0–1) indicating data quality.

**Verdict:** A (≥80), B (60–79), C (<60).
**Batch size:** 20 leads per scoring pass.

## Data Operations

Use **pandas** for batch scoring and analysis, **jq** for JSON I/O:

```python
import pandas as pd
import json

# Load leads into a DataFrame
with open(f"{campaign_dir}/raw_leads.json") as f:
    leads = pd.DataFrame(json.load(f))

with open(f"{campaign_dir}/icp_schema.json") as f:
    icp = json.load(f)

# SMB: vectorized pass/fail
leads["verdict"] = "fail"
mask = (
    leads["company_industry"].isin(icp["industries"]) &
    leads["company_size"].astype(int).between(icp["employee_range"]["min"], icp["employee_range"]["max"])
)
leads.loc[mask, "verdict"] = "pass"

# Mid-Market: weighted scoring
leads["fit_score"] = ...   # compute per rubric
leads["intent_score"] = ...
leads["timing_score"] = ...
leads["overall_score"] = leads["fit_score"] * 0.4 + leads["intent_score"] * 0.35 + leads["timing_score"] * 0.25
leads["verdict"] = pd.cut(leads["overall_score"], bins=[0, 50, 75, 100], labels=["C", "B", "A"])

# Summary stats
print(leads["verdict"].value_counts())
print(leads.nlargest(5, "overall_score")[["first_name", "last_name", "company_name", "overall_score"]])

# Save
leads.to_json(f"{campaign_dir}/scored_leads.json", orient="records", indent=2)
```

```bash
# Update pipeline state via jq
jq '.completed_steps += [4] | .current_step = 4' \
  "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
```

## Process

1. **Load inputs.** Use pandas `pd.DataFrame(json.load(...))` for `raw_leads.json`. Use jq or `json.load` for `icp_schema.json`, `pipeline_state.json`, and (if present) `market_kb.json`.

2. **Determine scoring mode** from `pipeline_state.json.company_scale`.

3. **Score in batches.** Use pandas vectorized operations to process leads in batches appropriate to the mode. Evaluate each lead against the rubric and assign scores as DataFrame columns.

4. **Enhance with market KB** (Mid / Enterprise only, if available): use buying triggers and competitor intel to enhance intent and timing scores via pandas merge/lookup.

5. **Assign verdicts.** Use `pd.cut` or boolean masks to apply thresholds and determine tier placement.

6. **Save output.** Use `df.to_json(..., orient="records")` to write `scored_leads.json` — each entry is the original lead record merged with its score object.

7. **Report summary** using pandas:
   - `df["verdict"].value_counts()` for verdict distribution
   - `df.nlargest(5, "overall_score")` for top-scoring leads preview
   - `df.groupby("company_industry")["verdict"].value_counts()` for patterns

8. **Update pipeline state.** Use jq to mark step 4 complete.

9. **Hand off.** For SMB, skip directly to `lead-intel`. For Mid / Enterprise, hand off to `account-deep-dive`.

## Output

Each entry in `scored_leads.json` combines the `lead_record` with a `score` field conforming to `reference/lead_score.schema.json` (bundled with this skill).

## Scoring Rubrics

- SMB: `reference/scoring_rubric_smb.md`
- Mid-Market: `reference/scoring_rubric_mid.md`
- Enterprise: `reference/scoring_rubric_enterprise.md`
