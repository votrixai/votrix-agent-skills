---
name: human-calibration
description: Review a sample of calibration leads, provide feedback to tune the pipeline before committing API credits
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
---

# Human Calibration (Skill 3.5)

Quality checkpoint between calibration pull and bulk pull. Shows diverse lead samples for human review to ensure targeting is on track before spending API credits.

## Prerequisites

- `calibration_leads.json` must exist in the campaign directory
- `icp_schema.json` must exist in the campaign directory

## Process

1. **Load calibration leads**: Read `calibration_leads.json` from campaign directory.

2. **Select diverse samples**: Pick 5 leads that represent diversity across:
   - Different companies (no duplicates)
   - Different title levels (mix of seniority)
   - Different industries (if multiple targeted)
   - Best and worst apparent fits

3. **Present each lead** with a clear card format:
   ```
   Lead 1/5
   ─────────────────────────
   Name:     Jane Smith
   Title:    VP of Marketing
   Company:  Acme Corp (SaaS, 150 employees)
   Location: San Francisco, CA
   Email:    jane@acme.com (verified)
   LinkedIn: linkedin.com/in/janesmith
   ─────────────────────────
   ```

4. **Collect feedback per lead** using AskUserQuestion:
   - **Fit**: Great fit / Okay fit / Bad fit / Not sure
   - **Why**: Free-text reason (optional)

5. **Collect overall feedback**:
   - "Are you seeing the right kinds of companies?"
   - "Are the titles/seniority levels right?"
   - "Any industries or company types to exclude?"
   - "Should we adjust the employee size range?"
   - "Any other adjustments?"

6. **Generate calibration feedback**: Synthesize all feedback into `calibration_feedback.json`:
   ```json
   {
     "sample_reviews": [
       {
         "lead_id": "...",
         "verdict": "great_fit|okay_fit|bad_fit",
         "reason": "..."
       }
     ],
     "adjustments": {
       "add_titles": [],
       "remove_titles": [],
       "add_industries": [],
       "remove_industries": [],
       "adjust_employee_range": null,
       "add_exclusions": [],
       "notes": ""
     },
     "approved_for_bulk_pull": true
   }
   ```

7. **Save and prompt**: Write `calibration_feedback.json` and tell the user to run `/apollo-prospector` again for the bulk pull.

## Key Principle

This is the **last chance to adjust** before API credits are spent on the bulk pull. Be thorough in collecting feedback and make sure the user explicitly approves before proceeding.
