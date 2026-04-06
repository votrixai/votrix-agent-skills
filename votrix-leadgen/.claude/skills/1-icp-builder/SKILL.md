---
name: icp-builder
description: Build your Ideal Customer Profile — define company scale, industries, personas, and targeting criteria
user-invocable: true
argument-hint: "<campaign-dir>"
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
---

# ICP Builder (Skill 1)

Builds the Ideal Customer Profile (ICP) that drives targeting for the rest of the pipeline.

## Prerequisites

- `business_context.json` must exist in the campaign directory

## Process

1. **Load business context**: Read `business_context.json` from the campaign directory.

2. **Determine company scale** (critical — this drives the entire pipeline):
   Ask the user to select their target company size:
   - **SMB** (1-200 employees): Pass/fail scoring, basic intel, Apollo-only
   - **Mid-Market** (200-2000 employees): 3D scoring, account research, Tavily+Firecrawl
   - **Enterprise** (2000+ employees): 4D scoring, full enrichment, all APIs

3. **Gather ICP criteria**:
   - **Industries**: Which industries to target? (suggest based on business_context)
   - **Employee range**: Min/max employee count
   - **Revenue range**: Min/max revenue (optional)
   - **Personas**: For each persona:
     - Title patterns (e.g., "VP of Marketing", "Head of Growth")
     - Seniority levels (c_suite, vp, director, manager, senior)
     - Departments (marketing, engineering, sales, etc.)
   - **Geography**: Countries and regions
   - **Technologies**: Tech stack filters (optional)
   - **Exclusions**: Companies, domains, or industries to exclude
   - **Lead volume target**: How many qualified leads do they want? (apply defaults from `scale_defaults.json`)

4. **Apply scale defaults**: Load `reference/scale_defaults.json` and suggest sensible defaults based on selected company_scale. User can override.

5. **Validate and confirm**: Show complete ICP summary, ask for confirmation.

6. **Save outputs**:
   - Write `icp_schema.json` to campaign directory
   - Update `pipeline_state.json` (set company_scale, mark step 1 complete)

## Schema

Output must conform to `config/schemas/icp_schema.schema.json`.

## Scale Defaults

Reference `reference/scale_defaults.json` for default values per company scale tier.

## Examples

See `examples/` for ICP examples at each scale tier.
