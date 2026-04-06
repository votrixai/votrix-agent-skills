---
name: apollo-prospector
description: Search Apollo.io for leads matching your ICP — calibration pull first, then bulk pull after human review
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
  - mcp__composio__*
---

# Apollo Prospector (Skill 3)

Pulls leads from Apollo.io based on the ICP schema. Uses a two-phase approach: calibration pull (small sample) then bulk pull (after human approval).

## Prerequisites

- `icp_schema.json` must exist in the campaign directory
- Composio MCP server configured with Apollo.io app connected
- Run `npx @composio/mcp setup apolloio` first if Apollo isn't connected yet

## Apollo Integration via Composio MCP

Apollo.io is accessed through the Composio MCP server. Use the Composio Apollo tools to search for people matching the ICP criteria.

### Available Composio Apollo Actions

- **People search**: Search for contacts by title, seniority, company size, industry, location
- **Organization search**: Look up company details
- **Contact enrichment**: Get email and phone data

### Field Mapping (Apollo response → lead_record schema)

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

1. **Load ICP**: Read `icp_schema.json` from the campaign directory using Read.

2. **Build search parameters**: Translate ICP criteria into Apollo search parameters:
   - Map `personas[].title_patterns` → person title search
   - Map `personas[].seniority` → seniority filter
   - Map `industries` → industry filter
   - Map `employee_range` → employee count range
   - Map `geo.countries` → location filter
   - Map `technologies` → technology filter
   - Apply exclusions

3. **Save query params**: Write `apollo_query_params.json` for audit trail using Write.

4. **Execute calibration pull**: Use Composio Apollo people search with limit set to calibration sample size (from `scale_defaults.json`, typically 50).

5. **Transform and save**: Map response to lead_record schema format, write to `calibration_leads.json` using Write.

6. **Report**: Tell user how many leads were found, show a quick summary (title distribution, company distribution), and prompt them to run `/human-calibration`.

### Phase 2: Bulk Pull (after calibration feedback)

1. **Check for feedback**: Read `calibration_feedback.json` from campaign directory using Read.

2. **Adjust search**: Apply any feedback-driven adjustments to search parameters.

3. **Execute bulk pull**: Use Composio Apollo people search with full `lead_volume_target` limit. Paginate if needed.

4. **Deduplicate**: Remove any leads already in `calibration_leads.json` (match on `lead_id`).

5. **Save raw leads**: Write combined results to `raw_leads.json` using Write.

6. **Update pipeline state**: Read `pipeline_state.json`, update Apollo credits used, mark step 3 complete, write back using Write.

## Apollo API Reference

See `reference/apollo_api_reference.md` for endpoint details, parameters, and rate limits.

## Output Schema

Each lead in the output must conform to `config/schemas/lead_record.schema.json`.
