---
name: apollo-prospector
description: Search Apollo.io for leads matching your ICP — calibration pull first, then bulk pull after human review
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

# Apollo Prospector (Skill 3)

Pulls leads from Apollo.io based on the ICP schema. Uses a two-phase approach: calibration pull (small sample) then bulk pull (after human approval).

## Prerequisites

- `icp_schema.json` must exist in the campaign directory
- `APOLLO_API_KEY` must be set in `.env`

## Apollo API Integration

Since Apollo does not have an MCP server, use Bash with curl to call the API directly.

### API Call Pattern

```bash
curl -s -X POST "https://api.apollo.io/v1/mixed_people/search" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d '<query_json>'
```

Read the API key from `.env` before making calls. See `reference/apollo_api_reference.md` for full parameter details.

### Response Handling

After receiving the API response:
1. Read the JSON response using Read (save raw response to a temp file first via Write)
2. Transform each person record into the `lead_record` schema format
3. Write the transformed array to the output file using Write

**Field mapping** (Apollo → lead_record):
- `id` → `lead_id`
- `first_name` → `first_name`
- `last_name` → `last_name`
- `title` → `title`
- `seniority` → `seniority`
- `departments[0]` → `department`
- `organization.name` → `company_name`
- `organization.website_url` → `company_domain`
- `organization.industry` → `company_industry`
- `organization.estimated_num_employees` → `company_size` (as string)
- `organization.annual_revenue` → `company_revenue` (as string)
- `organization.city + state + country` → `company_location`
- `organization.linkedin_url` → `company_linkedin_url`
- `linkedin_url` → `linkedin_url`
- `email` → `email`
- `email_status` → `email_status`
- `phone_numbers[0].raw_number` → `phone`
- `organization.current_technologies[].name` → `technologies`
- Set `source` = `"apollo"`, `pulled_at` = current ISO timestamp

## Process

### Phase 1: Calibration Pull

1. **Load ICP**: Read `icp_schema.json` from the campaign directory.

2. **Build Apollo query**: Translate ICP criteria into Apollo API parameters:
   - Map `personas[].title_patterns` → `person_titles`
   - Map `personas[].seniority` → `person_seniorities`
   - Map `industries` → `organization_industry_tag_ids` or keywords
   - Map `employee_range` → `organization_num_employees_ranges`
   - Map `geo.countries` → `person_locations`
   - Map `technologies` → `q_organization_keyword_tags`
   - Apply exclusions

3. **Save query params**: Write `apollo_query_params.json` for audit trail using Write.

4. **Execute calibration pull**: Call Apollo API via Bash+curl with `per_page` set to calibration sample size (from `scale_defaults.json`, typically 50).

5. **Transform and save**: Map response to lead_record schema, write to `calibration_leads.json` using Write.

6. **Report**: Tell user how many leads were found, show a quick summary (title distribution, company distribution), and prompt them to run `/human-calibration`.

### Phase 2: Bulk Pull (after calibration feedback)

1. **Check for feedback**: Read `calibration_feedback.json` from campaign directory.

2. **Adjust query**: Apply any feedback-driven adjustments to Apollo query params.

3. **Execute bulk pull**: Call Apollo API with full `lead_volume_target` limit. Paginate if needed (max 100 per page).

4. **Deduplicate**: Remove any leads already in `calibration_leads.json` (match on `lead_id`).

5. **Save raw leads**: Write combined results to `raw_leads.json` using Write.

6. **Update pipeline state**: Read `pipeline_state.json`, update Apollo credits used, mark step 3 complete, write back.

## Apollo API Reference

See `reference/apollo_api_reference.md` for endpoint details, parameters, and rate limits.

## Output Schema

Each lead in the output must conform to `config/schemas/lead_record.schema.json`.
