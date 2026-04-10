---
name: market-intel
description: Research the target market — industry trends, competitor intelligence, and buying triggers — using the Tavily MCP server for search and Firecrawl MCP server for scraping. Invoke this for mid-market and enterprise campaigns after icp-builder. Skip for SMB.
---

# Market Intelligence

Builds a market knowledge base by researching industry trends, competitor positioning, and buying triggers. This enriches downstream scoring (`lead-scorer`) and intel generation (`lead-intel`).

## When to Run

- **Mid-Market** campaigns: yes
- **Enterprise** campaigns: yes
- **SMB** campaigns: **skip** — return immediately, this adds cost without changing SMB pass/fail scoring

## Prerequisites

- `business_context.json` and `icp_schema.json` must exist in the campaign directory.
- The Tavily and Firecrawl MCP servers must be attached to the agent.

## Tools

- **Tavily MCP server** — search tool. Pass a query string, receive structured results (title, URL, content snippet, relevance score).
- **Firecrawl MCP server** — scrape tool. Pass a URL, receive markdown content of the page.

Use whichever tool names each MCP server exposes at runtime.

## Data Operations

Use **jq** for all JSON manipulation:

```bash
# Load inputs
BUSINESS=$(jq '.' "$CAMPAIGN_DIR/business_context.json")
ICP=$(jq '.' "$CAMPAIGN_DIR/icp_schema.json")

# Build the market KB JSON
jq -n \
  --arg generated_at "$(date -u +%FT%TZ)" \
  --argjson trends "$TRENDS_JSON" \
  --argjson competitors "$COMPETITOR_JSON" \
  --argjson triggers "$TRIGGERS_JSON" \
  --argjson sources "$SOURCES_JSON" \
  '{generated_at: $generated_at, industry_trends: $trends, competitor_intel: $competitors, buying_triggers: $triggers, sources_consulted: $sources}' \
  > "$CAMPAIGN_DIR/market_kb.json"

# Update pipeline state
jq '.completed_steps += [2] | .current_step = 2 | .credits_used.tavily += $t | .credits_used.firecrawl += $f' \
  --argjson t "$TAVILY_COUNT" --argjson f "$FIRECRAWL_COUNT" \
  "$CAMPAIGN_DIR/pipeline_state.json" > tmp.json && mv tmp.json "$CAMPAIGN_DIR/pipeline_state.json"
```

## Process

1. **Load inputs.** Use jq to read `business_context.json` and `icp_schema.json`.

2. **Generate search queries** using templates from `reference/query_templates.md`:
   - Industry trend queries (2–3 per target industry)
   - Competitor research queries (1–2 per known competitor)
   - Buying trigger queries (2–3 based on pain points)
   - Technology adoption queries (1–2 based on tech stack)

3. **Execute Tavily searches** for each query via the Tavily MCP server. Parse results for relevant insights. Track the number of searches made.

4. **Deep scrape key pages.** For high-value results, use the Firecrawl MCP server to extract full content:
   - Competitor pricing / feature pages
   - Industry report landing pages
   - Relevant news articles
   Track number of scrapes made.

5. **Synthesize into a market KB.** Use jq to build a structured JSON object containing:
   - **Industry trends** — key trends affecting target industries, with relevance ratings
   - **Competitor intel** — positioning, weaknesses, recent news per competitor
   - **Buying triggers** — events / signals that indicate buying readiness
   - **Market sizing** — TAM / SAM estimates if data is available

6. **Save output.** Use jq to write `market_kb.json`, conforming to `reference/market_kb.schema.json`. Include `generated_at` timestamp and `sources_consulted` list.

7. **Report summary.** Use jq to extract top 3 trends, competitor weaknesses, strongest buying triggers.

8. **Update pipeline state.** Use jq to update `pipeline_state.json` — increment Tavily/Firecrawl credit counters, mark step 2 complete.

## Query Templates

See `reference/query_templates.md`.

## Cost Management

- Tavily: aim for 10–20 searches total
- Firecrawl: aim for 5–10 page scrapes total
- Prioritize queries that will most impact scoring and intel quality
