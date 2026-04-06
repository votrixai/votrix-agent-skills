---
name: market-intel
description: Research your target market — industry trends, competitor intelligence, and buying triggers via MCP-integrated search and scraping
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - WebSearch
  - WebFetch
  - mcp__tavily__search
  - mcp__firecrawl__scrape
---

# Market Intelligence (Skill 2)

Builds a market knowledge base by researching industry trends, competitor positioning, and buying triggers. This enriches downstream scoring and intel generation.

## Prerequisites

- `business_context.json` must exist in the campaign directory
- `icp_schema.json` must exist in the campaign directory
- Tavily MCP server configured (for structured search)
- Firecrawl MCP server configured (for page scraping)

## MCP Tools

This skill uses MCP server integrations:

- **`mcp__tavily__search`**: Tavily search — pass a query string, receive structured results with titles, URLs, content snippets, and relevance scores
- **`mcp__firecrawl__scrape`**: Firecrawl scrape — pass a URL, receive markdown content of the page

## Process

1. **Load inputs**: Read `business_context.json` and `icp_schema.json` using Read.

2. **Generate search queries** using templates from `reference/query_templates.md`:
   - Industry trend queries (2-3 per target industry)
   - Competitor research queries (1-2 per known competitor)
   - Buying trigger queries (2-3 based on pain points)
   - Technology adoption queries (1-2 based on tech stack)

3. **Execute Tavily searches**: Use `mcp__tavily__search` for each query.
   - Parse results for relevant insights
   - Track number of searches made

4. **Deep scrape key pages**: For high-value results, use `mcp__firecrawl__scrape` to extract full content:
   - Competitor pricing/feature pages
   - Industry report landing pages
   - Relevant news articles
   - Track number of scrapes made

5. **Synthesize into market KB**: Analyze all gathered data and produce:
   - **Industry trends**: Key trends affecting target industries, with relevance ratings
   - **Competitor intel**: Positioning, weaknesses, recent news for each competitor
   - **Buying triggers**: Events/signals that indicate buying readiness
   - **Market sizing**: TAM/SAM estimates if data available

6. **Save output**: Write `market_kb.json` using Write, conforming to `config/schemas/market_kb.schema.json`. Include `generated_at` timestamp and `sources_consulted` list.

7. **Report summary**: Show key findings — top 3 trends, competitor weaknesses, and strongest buying triggers.

8. **Update pipeline state**: Read `pipeline_state.json`, update Tavily/Firecrawl credit counts, mark step 2 complete, write back using Write.

## Query Templates

See `reference/query_templates.md` for search query patterns.

## Cost Management

- Tavily: Aim for 10-20 searches total
- Firecrawl: Aim for 5-10 page scrapes total
- Prioritize queries that will most impact scoring and intel quality
