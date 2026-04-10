# Market Intel Query Templates

## Industry Trends

```
"{industry} trends {current_year}"
"{industry} challenges {current_year}"
"{industry} technology adoption trends"
"{industry} market outlook"
"top priorities for {persona_title} in {industry} {current_year}"
```

## Competitor Research

```
"{competitor_name} vs alternatives {current_year}"
"{competitor_name} reviews complaints"
"{competitor_name} pricing"
"{competitor_name} recent news"
"companies switching from {competitor_name}"
```

## Buying Triggers

```
"{industry} companies adopting {technology}"
"{industry} digital transformation initiatives"
"{pain_point} solutions for {industry}"
"{industry} budget priorities {current_year}"
"why companies invest in {product_category}"
```

## Technology Stack

```
"{technology} market share {industry}"
"{technology} alternatives comparison"
"companies using {technology} in {industry}"
"{technology} migration trends"
```

## Hiring Signals

```
"{industry} hiring trends {persona_department}"
"companies hiring {persona_title}"
```

## Usage Guidelines

1. Replace placeholders with values from `business_context.json` and `icp_schema.json`
2. Prioritize queries that directly inform scoring dimensions (Fit, Intent, Timing)
3. Start with industry trends (broadest context), then narrow to competitor-specific
4. Cap at 15-20 Tavily searches to manage costs
5. Only scrape pages (Firecrawl) that contain dense, valuable content
