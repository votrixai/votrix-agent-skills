# Lead Validation Rules

## Required Field Checks

### All Modes
| Field | Rule | Severity |
|-------|------|----------|
| `lead_id` | Must be non-empty string | ERROR |
| `first_name` | Must be non-empty string | ERROR |
| `last_name` | Must be non-empty string | ERROR |
| `email` | Must match email regex pattern | ERROR |
| `title` | Must be non-empty string | ERROR |
| `company_name` | Must be non-empty string | ERROR |

### Email Validation
- Must match pattern: `^[^\s@]+@[^\s@]+\.[^\s@]+$`
- Domain must not be a known disposable email provider
- `email_status` should be "verified" or "guessed" (warn on "unavailable")

### Deduplication
- No duplicate `lead_id` values
- No duplicate `email` values (keep the higher-scored entry)
- No duplicate `first_name + last_name + company_name` combos

## Score Validation

### SMB Mode
| Field | Rule | Severity |
|-------|------|----------|
| `score.verdict` | Must be "pass" or "fail" | ERROR |
| `score.score_mode` | Must be "smb_pass_fail" | ERROR |
| `score.rejection_reason` | Required if verdict is "fail" | WARN |

### Mid-Market Mode
| Field | Rule | Severity |
|-------|------|----------|
| `score.verdict` | Must be "A", "B", or "C" | ERROR |
| `score.score_mode` | Must be "mid_3d" | ERROR |
| `score.overall_score` | Must be 0-100 | ERROR |
| `score.dimensions.fit.score` | Must be 0-100 | ERROR |
| `score.dimensions.intent.score` | Must be 0-100 | ERROR |
| `score.dimensions.timing.score` | Must be 0-100 | ERROR |
| Verdict/score consistency | A≥75, B=50-74, C<50 | ERROR |

### Enterprise Mode
All mid-market rules plus:
| Field | Rule | Severity |
|-------|------|----------|
| `score.score_mode` | Must be "enterprise_4d" | ERROR |
| `score.dimensions.authority.score` | Must be 0-100 | ERROR |
| `score.dimensions.*.confidence` | Must be 0-1 for all dimensions | ERROR |
| Verdict/score consistency | A≥80, B=60-79, C<60 | ERROR |

## Intel Validation

### SMB
| Field | Rule | Severity |
|-------|------|----------|
| `pain_signal` | Required for "pass" leads | ERROR |
| `pain_signal` | Must be < 200 characters | WARN |
| `pain_signal` | Must be in question format (ends with ?) | WARN |

### Mid-Market (A and B tier)
| Field | Rule | Severity |
|-------|------|----------|
| `pain_signal` | Required | ERROR |
| `lead_intel` | Required, 2-3 sentences | WARN |
| `email_subject` | Required, < 60 chars | WARN |
| `email_opening` | Required, 1-2 sentences | WARN |

### Enterprise (A and B tier)
All mid-market rules plus:
| Field | Rule | Severity |
|-------|------|----------|
| `trigger_detail` | Required for A-tier | WARN |
| `email_cta` | Required | WARN |

## Severity Levels

- **ERROR**: Lead is excluded from CSV export. Issue is logged.
- **WARN**: Lead is included but issue is flagged in campaign summary.
