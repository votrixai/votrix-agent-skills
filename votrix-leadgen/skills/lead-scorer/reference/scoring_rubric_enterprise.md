# Enterprise Scoring Rubric — 4D Scoring

## Overview
Enterprise leads are scored on four dimensions (0-100 each) with confidence scores (0-1) per dimension. Weighted composite determines tier: A (≥80), B (60-79), C (<60).

## Dimension 1: Fit (30% weight)

Same criteria as mid-market, plus:

| Signal | Points | Max |
|--------|--------|-----|
| Exact title match to persona pattern | 25 | 25 |
| Company size in target range | 20 | 20 |
| Industry exact match | 15 | 15 |
| Technology overlap | 10 | 10 |
| Seniority level match | 10 | 10 |
| Organizational complexity match | 10 | 10 |
| Multi-division/global presence | 10 | 10 |

**Confidence factors**: Verified company data (high), self-reported (medium), inferred (low).

## Dimension 2: Intent (25% weight)

| Signal | Points | Max |
|--------|--------|-----|
| Strategic initiative announcements | 20 | 20 |
| RFP/RFI activity in space | 20 | 20 |
| Technology evaluation signals | 15 | 15 |
| Job postings in relevant area | 15 | 15 |
| Industry event participation | 10 | 10 |
| Content engagement signals | 10 | 10 |
| Competitor displacement indicators | 10 | 10 |

**Confidence factors**: Direct signals (high), inferred from news (medium), assumed from industry trends (low).

## Dimension 3: Timing (25% weight)

| Signal | Points | Max |
|--------|--------|-----|
| Budget cycle alignment | 20 | 20 |
| Fiscal year timing | 15 | 15 |
| Contract renewal window | 15 | 15 |
| Regulatory deadline | 15 | 15 |
| Board/strategic review period | 10 | 10 |
| New leadership mandate window | 15 | 15 |
| M&A integration period | 10 | 10 |

**Confidence factors**: Known budget cycle (high), industry-standard timing (medium), unknown (low).

## Dimension 4: Authority (20% weight)

Unique to enterprise — measures the lead's decision-making power.

| Signal | Points | Max |
|--------|--------|-----|
| C-suite title | 30 | 30 |
| VP-level title | 20 | 30 |
| Budget authority indicators | 25 | 25 |
| Reports to C-suite | 15 | 15 |
| Cross-functional influence | 15 | 15 |
| Known buying committee member | 15 | 15 |

**Confidence factors**: LinkedIn profile verified (high), title-inferred (medium), unknown (low).

## Composite Score Calculation

```
composite = (fit × 0.30) + (intent × 0.25) + (timing × 0.25) + (authority × 0.20)
```

## Tier Assignment

| Tier | Score Range | Action |
|------|------------|--------|
| A | ≥80 | High-touch outreach, full account deep dive, Proxycurl enrichment |
| B | 60-79 | Multi-channel outreach, selective deep dive |
| C | <60 | Nurture track or exclude |

## Output Format
```json
{
  "lead_id": "abc123",
  "score_mode": "enterprise_4d",
  "verdict": "A",
  "overall_score": 85,
  "dimensions": {
    "fit": { "score": 90, "confidence": 0.9, "rationale": "..." },
    "intent": { "score": 80, "confidence": 0.7, "rationale": "..." },
    "timing": { "score": 82, "confidence": 0.6, "rationale": "..." },
    "authority": { "score": 88, "confidence": 0.85, "rationale": "..." }
  },
  "scoring_notes": "Strong enterprise prospect with clear authority signal"
}
```
