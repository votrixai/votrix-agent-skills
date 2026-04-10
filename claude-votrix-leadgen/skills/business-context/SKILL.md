---
name: business-context
description: Interactive setup to capture the user's business profile, product, value proposition, and campaign goals. This is always the first step in a lead generation run — invoke it when the user wants to start or resume a B2B lead gen campaign and no business_context.json exists yet.
---

# Business Context Setup

You are setting up the business context for a B2B lead generation campaign. This is the first stage in the pipeline.

## Your Job

Interactively gather the user's business information and produce a validated `business_context.json` file in the session working directory.

## Process

1. **Check for existing context.** Look for an existing `business_context.json` (either in the session working directory or in any `output/<campaign>-<date>/` subdirectory). If found, ask the user whether to reuse it or start fresh.

2. **Gather information** by asking the user each of the following. Use structured multiple-choice prompts for enumerated options, and free-form questions for everything else:
   - **Company name** — what the company is called
   - **Product / service description** — 2–3 sentences on what it does
   - **Value proposition** — why customers choose it over alternatives
   - **Target customer description** — ideal customer in plain language
   - **Pain points solved** — 3–5 bullet points
   - **Competitors** — main competitors (optional but helpful)
   - **Outreach goal** — one of: `demo_booking`, `free_trial`, `consultation`, `partnership`, `other`
   - **Campaign name** — a short slug, e.g. `q2-saas-push`

3. **Validate and confirm.** Show the user a plain-text summary and ask for explicit confirmation before saving.

4. **Save output.** Use jq to construct and write `output/<campaign-name>-<YYYY-MM-DD>/business_context.json`:
   ```bash
   mkdir -p "output/<campaign-name>-<YYYY-MM-DD>"
   jq -n \
     --arg company "$COMPANY" \
     --arg product "$PRODUCT" \
     --arg value_prop "$VALUE_PROP" \
     --arg target "$TARGET" \
     --argjson pain_points "$PAIN_POINTS_ARRAY" \
     --argjson competitors "$COMPETITORS_ARRAY" \
     --arg goal "$GOAL" \
     --arg campaign "$CAMPAIGN_NAME" \
     '{company_name: $company, product_description: $product, value_proposition: $value_prop, target_customer: $target, pain_points: $pain_points, competitors: $competitors, outreach_goal: $goal, campaign_name: $campaign}' \
     > "output/<campaign-name>-<YYYY-MM-DD>/business_context.json"
   ```

5. **Initialize pipeline state.** Use jq to write `output/<campaign-name>-<YYYY-MM-DD>/pipeline_state.json`:
   ```json
   {
     "campaign_name": "<campaign-name>",
     "campaign_dir": "output/<campaign-name>-<YYYY-MM-DD>",
     "started_at": "<ISO timestamp>",
     "current_step": 0,
     "completed_steps": [0],
     "company_scale": null,
     "credits_used": { "apollo": 0, "tavily": 0, "firecrawl": 0 }
   }
   ```

6. **Report.** Tell the user the `campaign_dir` path and hand off — the next stage is the `icp-builder` skill.

## Schema

The output must conform to the business_context schema. Validate against `reference/business_context.schema.json` (bundled with this skill).

## Example

See `examples/business_context_example.json` for a complete example output.
