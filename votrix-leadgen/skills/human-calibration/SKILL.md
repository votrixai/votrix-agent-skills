---
name: human-calibration
description: Blocking quality checkpoint between Apollo calibration pull and bulk pull. Show a diverse sample of calibration leads to the user, collect feedback per lead and overall adjustments, then produce calibration_feedback.json. Invoke after apollo-prospector phase 1 completes, before phase 2.
---

# Human Calibration

Quality checkpoint between the Apollo calibration pull and the bulk pull. Shows diverse lead samples for human review to ensure targeting is on track **before** spending API credits on a full pull.

## Prerequisites

- `calibration_leads.json` must exist in the campaign directory (from `apollo-prospector` phase 1).
- `icp_schema.json` must exist in the campaign directory.

## Process

1. **Load calibration leads.** Use jq to read and query `calibration_leads.json`:
   ```bash
   # Load all leads
   jq '.' "$CAMPAIGN_DIR/calibration_leads.json"
   # Count by company
   jq 'group_by(.company_name) | map({company: .[0].company_name, count: length}) | sort_by(-.count)' "$CAMPAIGN_DIR/calibration_leads.json"
   # Pick 5 diverse samples
   jq '[group_by(.company_name) | .[] | .[0]] | .[0:5]' "$CAMPAIGN_DIR/calibration_leads.json"
   ```

2. **Select diverse samples.** Use jq to pick 5 leads that represent diversity across:
   - Different companies (no duplicates)
   - Different title levels (mix of seniority)
   - Different industries (if multiple targeted)
   - Best and worst apparent fits

3. **Present each lead** in a clear card format:
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

4. **Collect feedback per lead** via a structured multiple-choice prompt:
   - **Fit:** Great fit / Okay fit / Bad fit / Not sure
   - **Why:** free-text reason (optional)

5. **Collect overall feedback:**
   - Are you seeing the right kinds of companies?
   - Are the titles / seniority levels right?
   - Any industries or company types to exclude?
   - Should the employee size range be adjusted?
   - Any other adjustments?

6. **Generate calibration feedback.** Synthesize all feedback into `calibration_feedback.json`:
   ```json
   {
     "sample_reviews": [
       {
         "lead_id": "...",
         "verdict": "great_fit | okay_fit | bad_fit",
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

7. **Save and hand off.** Use jq to construct and write `calibration_feedback.json`:
   ```bash
   jq -n --argjson reviews "$REVIEWS_JSON" --argjson adjustments "$ADJUSTMENTS_JSON" --argjson approved "$APPROVED" \
     '{sample_reviews: $reviews, adjustments: $adjustments, approved_for_bulk_pull: $approved}' \
     > "$CAMPAIGN_DIR/calibration_feedback.json"
   ```
   If the user approved, hand off back to `apollo-prospector` for phase 2 (bulk pull). If not approved, tell the user what adjustments they should make to the ICP and hand back to `icp-builder`.

## Key Principle

This is the **last chance to adjust** before API credits are spent on the bulk pull. Be thorough in collecting feedback and make sure the user **explicitly approves** before proceeding. Never set `approved_for_bulk_pull: true` without a clear yes from the user.
