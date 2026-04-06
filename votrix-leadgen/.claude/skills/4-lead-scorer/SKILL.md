---
name: lead-scorer
description: Score leads against your ICP — SMB pass/fail, Mid-Market 3D, or Enterprise 4D scoring
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# Lead Scorer (Skill 4)

Scores each lead against the ICP. Scoring mode is determined by `company_scale` in `pipeline_state.json`.

## Prerequisites

- `raw_leads.json` must exist in the campaign directory
- `icp_schema.json` must exist in the campaign directory
- `pipeline_state.json` must exist with `company_scale` set
- `market_kb.json` (optional, Mid/Enterprise — enhances scoring if available)

## Scoring Modes

### SMB: Pass/Fail (`company_scale: "smb"`)

Binary scoring — does this lead match the ICP or not?

**Criteria** (see `reference/scoring_rubric_smb.md`):
- Title matches persona patterns → required
- Company size within range → required
- Industry matches → required
- Geography matches → required
- Email is verified or guessed → preferred but not required

**Verdict**: `pass` or `fail` with `rejection_reason`

**Batch size**: 50 leads per scoring call

### Mid-Market: 3D Scoring (`company_scale: "mid"`)

Three-dimensional scoring on 0-100 scale:

1. **Fit** (40% weight): Title match, company size, industry, technology overlap
2. **Intent** (35% weight): Recent activity signals, hiring patterns, tech changes
3. **Timing** (25% weight): Funding events, leadership changes, expansion signals

**Verdict**: A (≥75), B (50-74), C (<50)

**Batch size**: 30 leads per scoring call

### Enterprise: 4D Scoring (`company_scale: "enterprise"`)

Four-dimensional scoring with confidence scores:

1. **Fit** (30% weight): Same as mid + organizational complexity match
2. **Intent** (25% weight): Same as mid + strategic initiative alignment
3. **Timing** (25% weight): Same as mid + budget cycle indicators
4. **Authority** (20% weight): Decision-making power, org chart position, buying committee role

Each dimension includes a `confidence` score (0-1) indicating data quality.

**Verdict**: A (≥80), B (60-79), C (<60)

**Batch size**: 20 leads per scoring call

## Process

1. **Load inputs**: Read `raw_leads.json`, `icp_schema.json`, `pipeline_state.json`, and optionally `market_kb.json`.

2. **Determine scoring mode** from `pipeline_state.json.company_scale`.

3. **Score in batches**: Process leads in batches appropriate to the scoring mode. For each lead, evaluate against the rubric and assign scores.

4. **If market_kb.json is available** (mid/enterprise): Use buying triggers and competitor intel to enhance intent and timing scores.

5. **Assign verdicts**: Apply thresholds to determine tier placement.

6. **Save output**: Write `scored_leads.json` — each entry is the original lead record merged with its score object.

7. **Report summary**:
   - Total leads scored
   - Verdict distribution (pass/fail counts or A/B/C breakdown)
   - Top-scoring leads preview
   - Any notable patterns

8. **Update pipeline state**: Mark step 4 complete.

## Output

Each entry in `scored_leads.json` combines the `lead_record` with a `score` field conforming to `config/schemas/lead_score.schema.json`.

## Scoring Rubrics

- SMB: `reference/scoring_rubric_smb.md`
- Mid-Market: `reference/scoring_rubric_mid.md`
- Enterprise: `reference/scoring_rubric_enterprise.md`
