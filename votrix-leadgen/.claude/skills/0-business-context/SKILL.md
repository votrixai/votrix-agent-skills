---
name: business-context
description: Interactive setup to capture your business profile, product, value proposition, and campaign goals for lead generation
user-invocable: true
argument-hint: "[campaign-name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

# Business Context Setup (Skill 0)

You are setting up the business context for a B2B lead generation campaign. This is the first step in the pipeline.

## Your Job

Interactively gather the user's business information and output a validated `business_context.json` file.

## Process

1. **Check for existing context**: Look in the output directory for any existing `business_context.json`. If found, ask if the user wants to reuse or start fresh.

2. **Gather information** by asking the user these questions (use AskUserQuestion for structured choices, direct conversation for free-text):

   - **Company name**: What's your company called?
   - **Product/service description**: What does your product or service do? (2-3 sentences)
   - **Value proposition**: Why do customers choose you over alternatives?
   - **Target customer description**: Describe your ideal customer in plain language
   - **Pain points solved**: What problems does your product solve? (list 3-5)
   - **Competitors**: Who are your main competitors? (optional but helpful)
   - **Outreach goal**: What's the primary goal of this campaign?
     - Options: demo_booking, free_trial, consultation, partnership, other
   - **Campaign name**: A short slug for this campaign (e.g., "q2-saas-push")

3. **Validate and confirm**: Show the user a summary and ask for confirmation before saving.

4. **Save output**: Write to `output/<campaign-name>-<YYYY-MM-DD>/business_context.json`

5. **Initialize pipeline state**: Create `output/<campaign-name>-<YYYY-MM-DD>/pipeline_state.json` with:
   ```json
   {
     "campaign_name": "<campaign-name>",
     "campaign_dir": "output/<campaign-name>-<YYYY-MM-DD>",
     "started_at": "<ISO timestamp>",
     "current_step": 0,
     "completed_steps": [0],
     "company_scale": null,
     "credits_used": { "apollo": 0, "tavily": 0, "firecrawl": 0, "proxycurl": 0 }
   }
   ```

## Schema

The output must conform to `config/schemas/business_context.schema.json`.

## Arguments

If a campaign name is provided as an argument, use it directly instead of asking.

## Example

See `examples/business_context_example.json` for a complete example output.
