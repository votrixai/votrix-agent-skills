# SMB Scoring Rubric — Pass/Fail

## Overview
SMB scoring is binary: each lead either passes or fails. This keeps the process fast and high-volume.

## Required Criteria (all must pass)

### 1. Title Match
- Lead's title must match at least one pattern in `icp_schema.personas[].title_patterns`
- Matching is case-insensitive and supports partial matches
- Example: Pattern "VP of Marketing" matches "VP, Marketing" or "Vice President of Marketing"
- **Fail reason**: "Title does not match any ICP persona patterns"

### 2. Company Size
- Lead's `company_size` must fall within `icp_schema.employee_range`
- If employee count is unknown, check if other signals (revenue, industry) suggest fit
- **Fail reason**: "Company size outside ICP range (X employees vs. Y-Z target)"

### 3. Industry Match
- Lead's `company_industry` must match one of `icp_schema.industries`
- Allow fuzzy matching (e.g., "Computer Software" matches "SaaS")
- **Fail reason**: "Industry 'X' not in ICP target industries"

### 4. Geography Match
- Lead's location must match `icp_schema.geo.countries` and optionally `regions`
- **Fail reason**: "Location 'X' outside target geography"

## Preferred Criteria (noted but don't cause failure)

### 5. Email Quality
- `verified` email → best
- `guessed` email → acceptable
- `unavailable` email → flag but don't fail

### 6. Technology Overlap
- If `icp_schema.technologies` is set, note overlap percentage
- Not a pass/fail criterion for SMB

## Exclusion Checks
- If lead's company matches `icp_schema.exclusions.companies` → fail
- If lead's domain matches `icp_schema.exclusions.domains` → fail
- If lead's industry matches `icp_schema.exclusions.industries` → fail
- **Fail reason**: "Company/domain/industry is in exclusion list"

## Output Format
```json
{
  "lead_id": "abc123",
  "score_mode": "smb_pass_fail",
  "verdict": "pass",
  "rejection_reason": null,
  "scoring_notes": "Strong title match, company in range, verified email"
}
```
