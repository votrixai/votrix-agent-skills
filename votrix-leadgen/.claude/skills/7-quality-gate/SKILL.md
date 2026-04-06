---
name: quality-gate
description: Validate leads, export to CSV, and generate campaign intelligence summary
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
---

# Quality Gate & Export (Skill 7)

Final pipeline stage. Validates all lead data, exports to CSV, generates campaign intelligence JSON and human-readable summary.

## Prerequisites

- `intel_leads.json` must exist in the campaign directory
- `icp_schema.json` must exist in the campaign directory
- `pipeline_state.json` must exist in the campaign directory
- `business_context.json` must exist in the campaign directory

## Process

1. **Load inputs**: Read `intel_leads.json`, `icp_schema.json`, `pipeline_state.json` using Read.

2. **Validate each lead** against `reference/validation_rules.md`:
   - Required fields present and non-empty
   - Email format valid (regex: `^[^\s@]+@[^\s@]+\.[^\s@]+$`)
   - No duplicate lead_ids
   - No duplicate emails (keep higher-scored entry)
   - Score data present and consistent with scoring mode
   - Intel fields present for qualifying leads
   - Flag any data quality issues as ERROR or WARN

3. **Generate validation report** (include in campaign summary):
   - Total leads processed
   - Leads passing validation
   - Leads with warnings (minor issues)
   - Leads failing validation (excluded from export)
   - List specific issues for failed leads

4. **Export CSV** using Write:

   Build the CSV content directly — construct the header row and data rows based on `company_scale`. Use Write to save `leads.csv`.

   **CSV escaping rules**: Replace commas with semicolons in field values, replace newlines with spaces, wrap fields containing special characters in quotes.

   Sort leads by score (highest first for mid/enterprise) or verdict (pass first for SMB).

5. **Generate campaign_intel.json**: Build the full intelligence payload conforming to `config/schemas/campaign_intel.schema.json`. Write using Write.

6. **Generate campaign_summary.txt**: Build a human-readable summary using Write:
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
   • {verdict breakdown}

   TOP COMPANIES
   • {top 5 companies by lead count}

   TOP TITLES
   • {top 5 titles by frequency}

   API USAGE
   • Apollo: {N} credits
   • Tavily: {N} searches
   • Firecrawl: {N} scrapes
   • Proxycurl: {N} lookups

   OUTPUT FILES
   • leads.csv — {N} qualified leads
   • campaign_intel.json — full intelligence payload
   • campaign_summary.txt — this file
   ═══════════════════════════════════════
   ```

7. **Update pipeline state**: Read `pipeline_state.json`, mark step 7 complete, write back.

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

See `reference/validation_rules.md` for detailed validation criteria.
