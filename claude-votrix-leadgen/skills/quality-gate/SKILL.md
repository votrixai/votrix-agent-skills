---
name: quality-gate
description: Final pipeline stage — validate all lead data, export qualified leads to CSV, and generate campaign intelligence JSON plus a human-readable summary. Invoke after lead-intel produces intel_leads.json.
---

# Quality Gate & Export

Final pipeline stage. Validates lead data, exports to CSV, and generates a campaign intelligence payload plus a human-readable summary.

## Prerequisites

- `intel_leads.json`, `icp_schema.json`, `pipeline_state.json`, and `business_context.json` must exist in the campaign directory.

## Data Operations

Use **pandas** for validation, CSV export, and summary stats. Use **jq** for JSON I/O and pipeline state updates.

```python
import pandas as pd
import json, re

campaign_dir = "<campaign_dir>"

# Load
with open(f"{campaign_dir}/intel_leads.json") as f:
    df = pd.DataFrame(json.load(f))
with open(f"{campaign_dir}/pipeline_state.json") as f:
    state = json.load(f)

scale = state["company_scale"]

# Validate
df["_valid"] = True
df["_issues"] = ""

# Email format
email_re = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
bad_email = ~df["email"].apply(lambda x: bool(email_re.match(str(x))))
df.loc[bad_email, "_valid"] = False
df.loc[bad_email, "_issues"] += "invalid_email; "

# Duplicate emails — keep higher scored
df = df.sort_values("overall_score" if scale != "smb" else "verdict", ascending=False)
df = df.drop_duplicates(subset="email", keep="first")
df = df.drop_duplicates(subset="lead_id", keep="first")

# Required fields
required = ["first_name", "last_name", "email", "title", "company_name"]
for col in required:
    empty = df[col].isna() | (df[col] == "")
    df.loc[empty, "_valid"] = False
    df.loc[empty, "_issues"] += f"missing_{col}; "

valid_df = df[df["_valid"]].copy()

# CSV columns by scale
SMB_COLS = ["first_name", "last_name", "email", "email_status", "title", "company_name",
            "company_industry", "company_size", "company_location", "linkedin_url", "verdict", "pain_signal"]
MID_COLS = SMB_COLS[:10] + ["verdict", "overall_score", "fit_score", "intent_score", "timing_score",
           "pain_signal", "lead_intel", "email_subject", "email_opening"]
ENT_COLS = MID_COLS + ["authority_score", "fit_confidence", "intent_confidence",
           "timing_confidence", "authority_confidence", "trigger_detail", "email_cta"]

cols = {"smb": SMB_COLS, "mid": MID_COLS, "enterprise": ENT_COLS}[scale]
valid_df[cols].to_csv(f"{campaign_dir}/leads.csv", index=False)

# Summary
print(f"Total: {len(df)}, Valid: {len(valid_df)}, Failed: {len(df) - len(valid_df)}")
print(valid_df["verdict"].value_counts())
print("Top companies:", valid_df["company_name"].value_counts().head(5))
print("Top titles:", valid_df["title"].value_counts().head(5))
```

```bash
# Update pipeline state via jq
jq '.completed_steps += [7] | .current_step = 7' \
  "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
```

## Process

1. **Load inputs.** Use pandas `pd.DataFrame(json.load(...))` for `intel_leads.json`. Use jq or `json.load` for `icp_schema.json` and `pipeline_state.json`.

2. **Validate each lead** using pandas against `reference/validation_rules.md`:
   - Use `df[col].isna()` for required field checks
   - Use `df["email"].apply(regex)` for email format validation
   - Use `df.drop_duplicates(subset="lead_id")` and `df.drop_duplicates(subset="email", keep="first")` for dedup
   - Add `_valid` and `_issues` columns to flag `ERROR` / `WARN`

3. **Generate validation report** using pandas value counts:
   - `len(df)` for total, `df["_valid"].sum()` for passing, etc.

4. **Export CSV** using `df[cols].to_csv(...)`:
   - Column list determined by `company_scale` (see CSV Columns by Scale below).
   - Pandas handles CSV escaping automatically.
   - Sort by score (`.sort_values("overall_score", ascending=False)`) or verdict before export.

5. **Generate campaign_intel.json.** Use jq to build the full intelligence payload conforming to `reference/campaign_intel.schema.json`.

6. **Generate campaign_summary.txt** — write a human-readable summary:
   ```
   ═══════════════════════════════════════
   CAMPAIGN SUMMARY: {campaign_name}
   Date: {date}
   Scale: {company_scale}
   ═══════════════════════════════════════

   LEAD VOLUME
   • Total leads pulled: {N}
   • Leads scored: {N}
   • Qualified leads exported: {N}

   QUALITY DISTRIBUTION
   • {verdict breakdown from df["verdict"].value_counts()}

   TOP COMPANIES
   • {df["company_name"].value_counts().head(5)}

   TOP TITLES
   • {df["title"].value_counts().head(5)}

   API USAGE
   • Apollo:    {credits_used.apollo} credits
   • Tavily:    {credits_used.tavily} searches
   • Firecrawl: {credits_used.firecrawl} scrapes

   OUTPUT FILES
   • leads.csv           — {N} qualified leads
   • campaign_intel.json — full intelligence payload
   • campaign_summary.txt — this file
   ═══════════════════════════════════════
   ```

7. **Update pipeline state.** Use jq to mark step 7 complete.

8. **Report.** Point the user at the three output files and recap the final counts.

## CSV Columns by Scale

### SMB
```
first_name, last_name, email, email_status, title, company_name, company_industry, company_size, company_location, linkedin_url, verdict, pain_signal
```

### Mid-Market
```
first_name, last_name, email, email_status, title, company_name, company_industry, company_size, company_location, linkedin_url, verdict, overall_score, fit_score, intent_score, timing_score, pain_signal, lead_intel, email_subject, email_opening
```

### Enterprise
```
first_name, last_name, email, email_status, title, company_name, company_industry, company_size, company_location, linkedin_url, verdict, overall_score, fit_score, intent_score, timing_score, authority_score, fit_confidence, intent_confidence, timing_confidence, authority_confidence, pain_signal, lead_intel, email_subject, email_opening, trigger_detail, email_cta
```

## Validation Rules

See `reference/validation_rules.md`.
