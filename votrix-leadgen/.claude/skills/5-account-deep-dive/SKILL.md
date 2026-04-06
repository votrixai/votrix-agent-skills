---
name: account-deep-dive
description: Deep research on top-scored accounts — company news, tech stack, hiring signals, and LinkedIn enrichment via MCP tools
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - WebSearch
  - WebFetch
  - mcp__tavily__search
  - mcp__firecrawl__scrape
  - mcp__proxycurl__lookup
---

# Account Deep Dive (Skill 5)

Performs deep research on top-scored accounts (A and B tier) to enrich leads with account-level intelligence. Skipped for SMB campaigns.

## Prerequisites

- `scored_leads.json` must exist in the campaign directory
- `pipeline_state.json` must exist with `company_scale` set to "mid" or "enterprise"
- Tavily MCP server configured
- Firecrawl MCP server configured
- Proxycurl MCP server configured (Enterprise only)

## MCP Tools

- **`mcp__tavily__search`**: Search for company news, tech stack, hiring signals, financial data
- **`mcp__firecrawl__scrape`**: Scrape specific pages for deep content (e.g., company blogs, press releases, job boards)
- **`mcp__proxycurl__lookup`**: LinkedIn profile enrichment for A-tier enterprise leads — career history, skills, connections

## Process

### Lead Selection

1. **Load scored leads**: Read `scored_leads.json` using Read.
2. **Filter for research**: Select leads with verdict "A" or "B".
3. **Deduplicate by company**: Group leads by `company_name`, research each company once.

### Research Per Company

For each unique company in the A/B lead set:

4. **Company news search** (Tavily MCP):
   - Search: `"{company_name} news {current_year}"`
   - Search: `"{company_name} funding announcement"`
   - Search: `"{company_name} expansion hiring"`
   - Extract: recent news headlines, funding events, expansion signals

5. **Tech stack research** (Tavily MCP + Firecrawl MCP):
   - Search: `"{company_name} technology stack"`
   - If relevant results found, scrape the best page via Firecrawl
   - Extract: current technologies, recent tech changes

6. **Hiring signals** (Tavily MCP):
   - Search: `"{company_name} hiring {relevant_department}"`
   - Extract: open roles, team growth indicators

7. **Financial signals** (Tavily MCP):
   - Search: `"{company_name} revenue growth OR funding"`
   - Extract: funding rounds, revenue milestones, financial health

### Enterprise: Proxycurl Enrichment

For enterprise campaigns, additionally:

8. **LinkedIn profile lookup** (Proxycurl MCP): For A-tier leads with `linkedin_url`:
   - Call `mcp__proxycurl__lookup` with the LinkedIn URL
   - Extract: career history, skills, mutual connections, recent activity
   - Enhances Authority dimension scoring and personalization

### Output

9. **Merge enrichment data** into lead records. For each lead, add an `account_research` object:
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

10. **Save output**: Write `enriched_leads.json` to campaign directory using Write.

11. **Report**: Summary of companies researched, key findings, API calls made.

12. **Update pipeline state**: Read `pipeline_state.json`, update credit counts, mark step 5 complete, write back.

## Cost Management

- Mid-market: ~3-5 Tavily searches per company, 1-2 Firecrawl scrapes
- Enterprise: Same + 1 Proxycurl lookup per A-tier lead
- Cap total research at budget-appropriate levels
