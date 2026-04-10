---
name: apollo-prospector
description: Search Apollo.io for leads matching the ICP via Composio. Two phases — calibration pull (small sample for human review) first, then bulk pull after the user approves the calibration. Invoke when icp_schema.json exists and leads need to be sourced.
---

# Apollo Prospector

Pulls leads from Apollo.io based on the ICP schema. Uses a two-phase approach: **calibration pull** (small sample) then **bulk pull** (after explicit human approval from the `human-calibration` stage).

## Prerequisites

- `icp_schema.json` must exist in the campaign directory.
- The Composio MCP server must be attached to the agent.

## Apollo Integration via Composio

Apollo.io is accessed through Composio's meta-tools. Follow this workflow:

1. **Discover tools.** Call `COMPOSIO_SEARCH_TOOLS` with queries like `{"use_case": "search people on Apollo"}`. This returns the exact tool slugs and input schemas.
2. **Ensure connection.** If `COMPOSIO_SEARCH_TOOLS` indicates no active Apollo connection, call `COMPOSIO_MANAGE_CONNECTIONS` with `{"toolkits": ["apollo"]}` and complete auth.
3. **Execute.** Call `COMPOSIO_MULTI_EXECUTE_TOOL` with the discovered tool slugs and arguments.

Expected Apollo actions (actual tool slugs discovered at runtime):
- **People search** — search for contacts by title, seniority, company size, industry, location
- **Organization search** — look up company details
- **Contact enrichment** — get email / phone data

### Field Mapping (Apollo response → lead_record schema)

Use jq to transform the raw Apollo response into the lead_record schema:

```bash
# Example jq transform for a single Apollo person record
jq '{
  lead_id: .id,
  first_name: .first_name,
  last_name: .last_name,
  title: .title,
  seniority: .seniority,
  department: .departments[0],
  company_name: .organization.name,
  company_domain: .organization.website_url,
  company_industry: .organization.industry,
  company_size: (.organization.estimated_num_employees | tostring),
  company_revenue: (.organization.annual_revenue | tostring),
  company_location: [.organization.city, .organization.state, .organization.country] | map(select(. != null)) | join(", "),
  company_linkedin_url: .organization.linkedin_url,
  linkedin_url: .linkedin_url,
  email: .email,
  email_status: .email_status,
  phone: .phone_numbers[0].raw_number,
  technologies: [.organization.current_technologies[].name],
  source: "apollo",
  pulled_at: (now | todate)
}'
```

## Data Operations

Use **jq** for all JSON read/write/transform operations:

```bash
# Read ICP
jq '.' "$CAMPAIGN_DIR/icp_schema.json"

# Save query params
echo "$QUERY_PARAMS_JSON" | jq '.' > "$CAMPAIGN_DIR/apollo_query_params.json"

# Transform and save leads
echo "$RAW_RESPONSE" | jq '[.people[] | {lead_id: .id, ...}]' > "$CAMPAIGN_DIR/calibration_leads.json"

# Deduplicate by lead_id
jq -s '.[0] + [.[1][] | select(.lead_id as $id | [.[0][] | .lead_id] | index($id) | not)]' \
  calibration_leads.json bulk_leads.json > raw_leads.json

# Update pipeline state
jq '.completed_steps += [3] | .current_step = 3 | .credits_used.apollo += $credits' \
  --argjson credits "$CREDITS_USED" "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
```

## Process

### Phase 1: Calibration Pull

1. **Load ICP.** `jq '.' "$CAMPAIGN_DIR/icp_schema.json"`

2. **Build search parameters.** Translate ICP criteria into Apollo search parameters:
   - `personas[].title_patterns` → person title search
   - `personas[].seniority` → seniority filter
   - `industries` → industry filter
   - `employee_range` → employee count range
   - `geo.countries` → location filter
   - `technologies` → technology filter
   - Apply exclusions

3. **Save query params.** Write `apollo_query_params.json` via jq for audit trail.

4. **Execute calibration pull.** Use `COMPOSIO_SEARCH_TOOLS` to discover the Apollo people search tool, then call it via `COMPOSIO_MULTI_EXECUTE_TOOL` with `limit` set to the calibration sample size (typically 50).

5. **Transform and save.** Use jq to map the response to lead_record schema and write to `calibration_leads.json`.

6. **Report and hand off.** Use jq to compute summary stats (title distribution, company distribution) and tell the user. Hand off to `human-calibration`. **Do not proceed to the bulk pull until `calibration_feedback.json` exists with `approved_for_bulk_pull: true`.**

### Phase 2: Bulk Pull (after calibration feedback)

1. **Check for feedback.** `jq '.approved_for_bulk_pull' "$CAMPAIGN_DIR/calibration_feedback.json"` — if not `true`, stop.

2. **Adjust search.** Use jq to merge feedback adjustments into query params.

3. **Execute bulk pull.** Call the Apollo people search tool via `COMPOSIO_MULTI_EXECUTE_TOOL` with the full `lead_volume_target` limit. Paginate if needed.

4. **Deduplicate.** Use jq to remove leads already in `calibration_leads.json` (match on `lead_id`).

5. **Save raw leads.** Use jq to merge and write `raw_leads.json`.

6. **Update pipeline state.** Use jq to update `pipeline_state.json` — increment Apollo credits, mark step 3 complete.

7. **Hand off** to the `lead-scorer` skill.

## Apollo API Reference

See `reference/apollo_api_reference.md` for endpoint details, parameters, and rate limits.

## Output Schema

Each lead in `raw_leads.json` must conform to `reference/lead_record.schema.json` (bundled with this skill).
