# Mid-Market Scoring Rubric — 3D Scoring

## Overview
Mid-market leads are scored on three dimensions (0-100 each), weighted to produce a composite score. Leads are tiered as A (≥75), B (50-74), or C (<50).

## Dimension 1: Fit (40% weight)

Measures how well the lead matches the ICP profile.

| Signal | Points | Max |
|--------|--------|-----|
| Exact title match to persona pattern | 30 | 30 |
| Fuzzy/partial title match | 15 | 30 |
| Company size in sweet spot (middle 50% of range) | 25 | 25 |
| Company size in range but at edges | 15 | 25 |
| Industry exact match | 20 | 20 |
| Industry adjacent match | 10 | 20 |
| Technology overlap (per matching tech) | 5 | 15 |
| Seniority level match | 10 | 10 |

## Dimension 2: Intent (35% weight)

Signals that suggest the lead/company is actively looking for a solution.

| Signal | Points | Max |
|--------|--------|-----|
| Job postings in relevant area | 20 | 20 |
| Technology changes (new tools adopted) | 20 | 20 |
| Content engagement (webinars, whitepapers) | 15 | 15 |
| Company growth rate > 20% YoY | 15 | 15 |
| Recent relevant news/PR | 15 | 15 |
| Competitor displacement signals | 15 | 15 |

*Note: Many intent signals require `market_kb.json` data. Without it, default to conservative scores (30-50 range).*

## Dimension 3: Timing (25% weight)

Indicators that the timing is right for outreach.

| Signal | Points | Max |
|--------|--------|-----|
| Recent funding round (<6 months) | 25 | 25 |
| New C-level hire (<3 months) | 20 | 20 |
| Fiscal year start/budget cycle | 15 | 15 |
| Recent expansion/new office | 15 | 15 |
| Competitor contract renewal window | 15 | 15 |
| Regulatory deadline approaching | 10 | 10 |

*Note: Timing signals often require external research. Score conservatively without enrichment data.*

## Composite Score Calculation

```
composite = (fit × 0.40) + (intent × 0.35) + (timing × 0.25)
```

## Tier Assignment

| Tier | Score Range | Action |
|------|------------|--------|
| A | ≥75 | Priority outreach, deep dive recommended |
| B | 50-74 | Standard outreach, selective deep dive |
| C | <50 | Low priority, review for exclusion |

## Output Format
```json
{
  "lead_id": "abc123",
  "score_mode": "mid_3d",
  "verdict": "A",
  "overall_score": 82,
  "dimensions": {
    "fit": { "score": 85, "rationale": "Exact title match, company in sweet spot" },
    "intent": { "score": 78, "rationale": "Active hiring in target department, tech stack overlap" },
    "timing": { "score": 80, "rationale": "Series B funding 3 months ago" }
  },
  "scoring_notes": "Strong fit with recent funding signal"
}
```
