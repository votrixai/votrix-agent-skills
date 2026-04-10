---
name: account-deep-dive
description: Deep research on top-scored accounts (A and B tier) using Tavily for search and Firecrawl for scraping via Composio. Enriches leads with company news, tech stack, hiring signals, and financial signals. Mid-market and enterprise only — skip for SMB.
---

# Account Deep Dive

Performs deep research on top-scored accounts (A and B tier) to enrich leads with account-level intelligence. **Skipped entirely for SMB campaigns.**

## When to Run

- **SMB:** skip
- **Mid-Market:** yes, for A and B leads
- **Enterprise:** yes, for A and B leads

## Prerequisites

- `scored_leads.json` must exist in the campaign directory.
- `pipeline_state.json` must exist with `company_scale` set to `"mid"` or `"enterprise"`.
- The Composio MCP server must be attached to the agent.

## Tools (via Composio)

Access Tavily and Firecrawl through Composio's meta-tools. Call `COMPOSIO_SEARCH_TOOLS` to discover tool slugs, ensure connections via `COMPOSIO_MANAGE_CONNECTIONS`, then execute via `COMPOSIO_MULTI_EXECUTE_TOOL`.

- **Tavily** — company news, tech stack, hiring signals, financial data
- **Firecrawl** — deep content from specific pages (blogs, press releases, job boards)

## Data Operations

Use **jq** for lead filtering, enrichment merging, and pipeline state updates:

```bash
# Filter A/B leads
jq '[.[] | select(.score.verdict == "A" or .score.verdict == "B")]' \
  "$CAMPAIGN_DIR/scored_leads.json" > /tmp/ab_leads.json

# Get unique companies
jq '[.[].company_name] | unique' /tmp/ab_leads.json

# Merge account_research into each lead by company
jq --argjson research "$RESEARCH_JSON" '
  [.[] | . + {account_research: ($research[.company_name] // {})}]
' "$CAMPAIGN_DIR/scored_leads.json" > "$CAMPAIGN_DIR/enriched_leads.json"

# Update pipeline state
jq '.completed_steps += [5] | .current_step = 5 | .credits_used.tavily += $t | .credits_used.firecrawl += $f' \
  --argjson t "$TAVILY_COUNT" --argjson f "$FIRECRAWL_COUNT" \
  "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
```

## Process

### Lead Selection

1. **Load scored leads.** Use jq to read `scored_leads.json`.
2. **Filter for research.** Use jq to select leads with verdict `A` or `B`.
3. **Deduplicate by company.** Use jq to extract unique `company_name` values; research each company once and fan results out to all leads from that company.

### Research Per Company

For each unique company in the A/B lead set:

4. **Company news search** (Tavily via Composio):
   - `"{company_name} news {current_year}"`
   - `"{company_name} funding announcement"`
   - `"{company_name} expansion hiring"`
   - Extract: recent headlines, funding events, expansion signals.

5. **Tech stack research** (Tavily + Firecrawl via Composio):
   - `"{company_name} technology stack"`
   - If a high-value result appears, scrape it via the Firecrawl tool using `COMPOSIO_MULTI_EXECUTE_TOOL`.
   - Extract: current technologies, recent tech changes.

6. **Hiring signals** (Tavily via Composio):
   - `"{company_name} hiring {relevant_department}"`
   - Extract: open roles, team growth indicators.

7. **Financial signals** (Tavily via Composio):
   - `"{company_name} revenue growth OR funding"`
   - Extract: funding rounds, revenue milestones, financial health.

### Output

8. **Merge enrichment data** into lead records using jq. For each lead, add an `account_research` object:
   ```json
   {
     "account_research": {
       "recent_news": ["headline 1", "headline 2"],
       "tech_stack": ["Tool A", "Tool B"],
       "hiring_signals": ["Hiring 3 SDRs", "New VP Sales role posted"],
       "financial_signals": ["Series B $20M, March 2024"]
     }
   }
   ```

9. **Save output.** Write `enriched_leads.json` via jq.

10. **Report.** Use jq to summarize companies researched, key findings, API call counts.

11. **Update pipeline state.** Use jq to update `pipeline_state.json` — increment Tavily/Firecrawl credits, mark step 5 complete.

12. **Hand off** to `lead-intel`.

## Cost Management

- Mid-market: ~3–5 Tavily searches per company, 1–2 Firecrawl scrapes
- Enterprise: same budget unless you have reason to go deeper
- Cap total research at budget-appropriate levels for the configured `lead_volume_target`
