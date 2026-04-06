---
name: lead-intel
description: Generate personalized outreach intelligence for each qualified lead — pain signals, email drafts, and trigger details
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - Bash
---

# Lead Intel (Skill 6)

Generates personalized outreach intelligence for each qualified lead. Output depth varies by company_scale.

## Prerequisites

- `scored_leads.json` must exist in the campaign directory
- `business_context.json` must exist in the campaign directory
- `icp_schema.json` must exist in the campaign directory
- `enriched_leads.json` (optional, Mid/Enterprise — from Skill 5)
- `market_kb.json` (optional — enhances intel quality)
- `pipeline_state.json` must exist with `company_scale` set

## Intel Modes

### SMB Mode

For each **passing** lead, generate:
- **`pain_signal`**: A question-format hook that surfaces a likely pain point
  - Format: "Are you still [doing painful thing] when you could [better outcome]?"
  - Keep it specific to their role and industry
  - Use Haiku-level generation for cost efficiency

**Input**: `scored_leads.json` (pass verdicts only)
**Batch**: Process all passing leads at once

### Mid-Market Mode

For each **A and B tier** lead, generate:
- **`pain_signal`**: Detailed pain hypothesis (not question format — statement)
- **`lead_intel`**: 2-3 sentence personalized insight connecting their situation to your solution
- **`email_subject`**: Suggested subject line (<60 chars, no clickbait)
- **`email_opening`**: First 1-2 sentences of a personalized cold email

**Input**: `enriched_leads.json` if available, else `scored_leads.json`
**Batch**: Process A-tier first, then B-tier

### Enterprise Mode

For each **A and B tier** lead, generate everything from Mid-Market plus:
- **`trigger_detail`**: Specific trigger event driving outreach timing (from account research)
- **`email_cta`**: Tailored call-to-action based on their authority level and likely priorities

**Input**: `enriched_leads.json` (should be available for A/B leads)
**Batch**: Process individually for maximum personalization

## Process

1. **Load inputs**: Read scored/enriched leads, business context, ICP, and market KB.

2. **Filter leads**: Only process leads that meet the mode's criteria:
   - SMB: verdict == "pass"
   - Mid/Enterprise: verdict in ["A", "B"]

3. **Generate intel**: For each qualified lead, use the business context and any available enrichment data to generate personalized outreach content.

4. **Apply templates**: Reference `reference/intel_templates.md` for tone, format, and quality guidelines.

5. **Save output**: Write `intel_leads.json` — each entry is the lead record merged with intel fields.

6. **Report summary**: Count of leads with intel generated, sample of best intel pieces.

7. **Update pipeline state**: Mark step 6 complete.

## Intel Templates

See `reference/intel_templates.md` for guidelines on tone, format, and quality.
