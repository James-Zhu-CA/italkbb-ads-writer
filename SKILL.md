---
name: italkbb-ads-writer
description: Generate Google Ads, Facebook Ads, and Xiaohongshu copy plus image and video creative prompts for iTalkBB offerings. Use when ad copy or creative prompts must be grounded in current product pages on www.italkbb.ca with verified promotion price, original price, feature facts, audience segmentation, and mandatory fresh fact-check before delivery.
---

# iTalkBB Ads Writer

## Overview

Create conversion-focused ad copy and creative prompts for Google Ads, Facebook Ads, and Xiaohongshu. Run one unified plan-first workflow from Step 0 to Step 7 with mandatory artifact files, including interactive package-price pages where prices appear only after selecting variants.

## Supported Output Types

- Google Ads copy (headlines, descriptions, short callouts) and Google image/video generation prompts.
- Facebook Ads copy and Facebook image/video generation prompts.
- Xiaohongshu copy and Xiaohongshu image/video generation prompts.

## Plan-First Execution Contract

- Start with Step 0 planning before any website search or fact extraction.
- Use `update_plan` as the first workflow action and track Step 0 to Step 7 states.
- Step 0 and Step 7 are mandatory for every run.
- In Step 0, decide which of Step 1 to Step 6 are required for the current request.
- Use Step Selection Decision Matrix in Step 0:
  - first-time copy generation: select Step 1 + Step 2 + Step 3 + Step 4 + Step 5 + Step 6
  - copy revision: select only needed steps based on revision scope
  - copy verification: select Step 1 only
  - other tasks: select steps flexibly based on request and dependency
- For non first-time generation tasks, do not force Step 1 to Step 6 full flow by default.
- Execute steps in plan order.
- For each selected step:
  - set status to `in_progress` before execution
  - set status to `completed` after execution
- For each unselected optional step (Step 1 to Step 6):
  - mark as `completed (skipped)` in plan tracking
  - record reason in `step0-plan.md`
- Hard gate: do not run `search/open/curl` for website facts or variant-state extraction before `step0-plan.md` is created.

## Artifact Location and Naming

- Use run folder: `workflow/<run-id>/`
- Use run id format: `YYYYMMDD-HHMMSS-<platform>-<product>`
- Mandatory artifacts (always required):
  - `workflow/<run-id>/step0-plan.md`
  - `workflow/<run-id>/step7-fact-check.md`
- Conditional artifacts (required only when that step is selected in Step 0):
  - `workflow/<run-id>/step1-scope.md`
  - `workflow/<run-id>/step2-facts.md`
  - `workflow/<run-id>/step3-persona.md`
  - `workflow/<run-id>/step4-pain-itch-delight.md`
  - `workflow/<run-id>/step5-selling-points.md`
  - `workflow/<run-id>/step6-platform-copy.md`
- Do not create optional step files for skipped steps. Record skipped-step reasons only in `step0-plan.md`.

## Artifact Structure (All Steps)

Each step artifact must contain:

- `## Step`
- `## Status`
- `## Inputs`
- `## Method`
- `## Output`
- `## Fact Map`
- `## Tool Trace`

For template-driven steps, add:

- `## Template Called`

For steps with price claims on interactive pages, add:

- `## Variant Context`

## Schema Contract (Step 3 to Step 7)

- Canonical persona keys are mandatory in all Step 3 to Step 7 structured outputs:
  - `persona_id`
  - `behavior archetype`
- `persona_id` format must be stable across the run (`P01`, `P02`, `P03`, ...).
- `segment background` or similar labels are supplementary persona attributes only.
- Never use `segment background` as a replacement for `persona_id` or `behavior archetype`.
- Pre-completion gate:
  - Step 3 cannot be marked `completed` if any required table misses `persona_id` + `behavior archetype`.
  - Step 4 to Step 7 cannot be marked `completed` if persona references do not map back to Step 3 `Target Segment List`.
- If schema mismatch is found, fix current step artifact before moving to next step.

## Official Source Domain Guard (Mandatory)

- Default official fact source domain for this skill is `www.italkbb.ca` only.
- For price, promotion, original price, and conditions claims:
  - allow sources under `https://www.italkbb.ca/...` only
  - reject `italkbb.com` pages as evidence by default to avoid cross-site price mismatch
- `italkbb.com` may be used only when the user explicitly requests `.com` market verification, and `.ca` / `.com` facts must be kept in separate claim sets and outputs.
- Step 0 must record `Allowed Fact Domains` in `step0-plan.md`.
- Step 1 canonical URL rule extension:
  - canonical product page must be under `www.italkbb.ca` unless user explicitly requests another domain
- Step 2 and Step 7 hard gate:
  - if fetched evidence URL is outside allowed fact domains, do not use it for claim validation
  - record it as rejected evidence in tool trace or fetch notes with reason `domain_not_allowed`

## Locked Business URL Registry and Cache (Mandatory for Listed Businesses)

- For the listed iTalkBB businesses in `references/business-url-registry.json`, do not search for product URLs in Step 0 or Step 1.
- Use the locked registry entry (`business_id` + locale) to map canonical/auxiliary official URLs.
- Registry policy:
  - user-locked `chs` URLs are the authoritative starting point
  - `cht` / `en` URLs may be auto-discovered from the `chs` page language switch and persisted back into the registry
- Cache root for website snapshots is the workspace project root `business_info/` directory.
- Use `scripts/business_info_cache.py` to fetch/cache listed business pages.
- Cache TTL default is 7 days:
  - if cache age is `<= 7` days, Step 2 may reuse cache
  - if cache age is `> 7` days, refresh from website before use
- Step 7 hybrid freshness rule (user-approved):
  - price / promotion / original price / conditions claims must force-refresh official website in the current run (do not rely only on 7-day cache)
  - feature/spec/general descriptive claims may reuse `<= 7` day cache
- `monthly_promotion` is an auxiliary promotion source and may conflict with product page pricing:
  - record source page per price claim
  - if conflict exists, mark `price_conflict` and surface warning; do not silently merge or overwrite claims

## Mandatory Workflow

### Step 0: Dynamic Plan Initialization

- Analyze request objective, platform, product, audience, and compliance sensitivity.
- Mark Step 0 and Step 7 as mandatory.
- Decide which steps from Step 1 to Step 6 are required for this run.
- Apply Step Selection Decision Matrix and record decision basis.
- For verification-only runs, keep optional-step selection to Step 1 unless user explicitly requests deeper analysis.
- Build document dependency map for this run:
  - which step file depends on which prior files
  - which official URLs must be fetched
  - whether request matches a locked business in `references/business-url-registry.json`
  - selected business_id and locale (if registry hit)
  - which tools/methods are needed (for example search/open/curl)
  - cache strategy (`business_info/` path, 7-day TTL, Step 7 price/promo force-refresh exception)
  - page display type status (`pending` in Step 0, finalize in Step 2)
  - variant traversal strategy draft for possible interactive pages
- Output `workflow/<run-id>/step0-plan.md` with:
  - request summary
  - step selection decision matrix result
  - selected optional steps and reasons
  - skipped optional steps and reasons
  - required documents and dependencies
  - execution queue (`Step 0 -> selected optional steps -> Step 7`)
  - official source URL list to be fetched
  - allowed fact domains
  - locked business registry match (`yes/no`) and `business_id` / locale (if matched)
  - cache root path and cache policy summary
  - tool strategy
  - page display type status (`pending`)
  - variant traversal checklist for Step 2 and Step 7
  - plan status table for Step 0 to Step 7
- Only after Step 0 is completed, continue to Step 1 or the next selected step.

### Step 1: Confirm Product, Service, and Platform

- Execute only if selected in Step 0.
- Allowed actions in Step 1:
  - identify requested platform and output format
  - identify product/service and map canonical product page URL
  - for listed businesses, map URLs from `references/business-url-registry.json` instead of search
  - confirm target audience and output quantity
  - run lightweight URL availability check
- Prohibited actions in Step 1:
  - price extraction
  - terms extraction
  - Nuxt chunk reverse lookup
  - payload parsing
  - claim-level validation
- URL check budget in Step 1:
  - at most one availability check per candidate URL
  - any deeper content extraction moves to Step 2
- Canonical URL rule:
  - for product promotion tasks, canonical must be product page (for example `.../chinese-tv-plans...`)
  - `promotion` and `legal` pages are Step 2 auxiliary evidence only and cannot be canonical in Step 1
- If product page is ambiguous, ask clarifying questions before continuing.
- Confirm and write:
  - platform + format
  - product/service name
  - canonical product page URL
  - preferred target audience segment (optional)
  - requested quantity
- Write scope decisions to `workflow/<run-id>/step1-scope.md`.

### Audience Segmentation and Language Policy (Mandatory)

- Step 1 target segment is optional and treated as a priority candidate only, not a final lock.
- Step 3 must derive personas from business and market signals with behavior-first segmentation (motivation, habit, scenario, decision path, JTBD).
- Do not use language or cultural background as the primary segmentation key.
- Language and cultural background must be included as one persona dimension, not the persona name itself.
- Do not force all candidate personas in every task; select relevant persona subset by product scope and market fit.
- Step 3 must finalize one explicit `Target Segment List` for this run.
- Step 4 to Step 6 must process all personas in `Target Segment List`; do not skip any selected target persona.
- Step 3 target-segment selection default rule:
  - if user does not explicitly request single-segment processing, include top 3 ranked personas from `Core Audience Scoring` in `Target Segment List`
  - if fewer than 3 valid personas exist, include all valid personas
  - if user explicitly requests single-segment processing, include only that persona
- `core audience` indicates execution priority only, not exclusion of other segments in `Target Segment List`.
- Segment language and script lock is derived from each persona's primary language usage:
  - Traditional Chinese dominant -> Traditional Chinese
  - Simplified Chinese dominant -> Simplified Chinese
  - English dominant -> English
- For each selected persona, explicitly define common language, language/cultural background, and script lock in Step 3 output.
- For each selected persona, Step 3 must also define a `Language Localization Profile` for downstream writing, including at minimum:
  - target locale/style variant (for example: HK-style Traditional Chinese / TW-style Traditional Chinese / Mainland-style Simplified Chinese / English business plain style)
  - tone + formality level
  - wording preferences (preferred terms/phrasing)
  - wording avoid list (cross-region or unnatural terms to avoid)
  - punctuation and formatting conventions
  - sentence rhythm/style notes (short/direct vs narrative/warm)
- Default locale/style rule when user does not explicitly specify writing style:
  - Hong Kong audience persona -> HK-style ad wording and tone
  - Taiwan audience persona -> TW-style ad wording and tone
  - Mainland audience persona -> Mainland-style ad wording and tone
  - North America English audience persona -> North America English ad wording and tone
  - If regional style is ambiguous, infer from Step 3 language/cultural background + scenario context, and record the rationale in `Language Localization Profile`.
- Do not mix Traditional Chinese, Simplified Chinese, and English in one persona output package.
- If Step 1 has preferred segment, include it as a priority candidate in Step 3 comparison; do not auto-select it as core.
- If Step 3 is selected, Step 6 language lock and localization rules must follow Step 3 selected persona(s). For multi-persona output, generate one language-locked package per persona.

### Step 2: Extract Latest Website Facts

- Execute only if selected in Step 0.
- Fetch facts from official pages confirmed in Step 1.
- Enforce `Allowed Fact Domains` from Step 0 before any fact extraction.
- For listed businesses, call `scripts/business_info_cache.py` first and use `business_info/` cache with 7-day TTL.
- Record cache decision (`hit` / `miss` / `stale_refresh`) in Step 2 fetch notes.
- Finalize page display type in Step 2 first half and lock it for downstream steps:
  - `static`: price visible directly in page content
  - `interactive-variant`: price changes only after selecting package or option
- After finalization, do not change page display type in Step 3 to Step 7.
- If page is `interactive-variant`, enumerate all selectable variants before writing facts.
- Build `Fetch Dedup Log` in `step2-facts.md`:
  - URL
  - fetched_at
  - purpose
  - allowed domain check (`pass` / `fail`)
  - cache status (`hit` / `miss` / `stale_refresh`)
  - cache file path (if used)
- Within Step 2, do not fetch same URL repeatedly for same purpose.
- If repeated fetch is unavoidable (timeout/5xx), record reason in `Fetch Dedup Log`.
- Extract:
  - promotional price, original price, conditions
  - value features and product benefits
  - restrictions and fee-related terms (contract, extra fees, termination fees, taxes, activation/device fees)
- Separate into two mandatory buckets:
  - `Value Features`
  - `Restrictions and Fees`
- For `interactive-variant` pages, build a mandatory `Variant Price Matrix` in `step2-facts.md`:
  - variant key/name
  - promo price
  - original price
  - conditions and restrictions
  - capture method (`UI-state` / `payload` / `endpoint`)
  - source URL and capture timestamp
- Nuxt/JS reverse lookup or payload parsing is allowed only when:
  - page is confirmed `interactive-variant`, and
  - required price/condition facts are not obtainable from DOM-visible content.
- Never treat `Restrictions and Fees` as selling points.
- If required fact is missing, mark `not found on page`.
- For verification tasks where Step 6 is not selected, optionally build a claim inventory from user-provided copy as Step 7 input.
- Write full extraction with URL evidence and extraction timestamp to `workflow/<run-id>/step2-facts.md`.

### Step 3: Build Target User Persona

- Execute only if selected in Step 0.
- Load `references/analysis-prompts.md`.
- Must call template `1) 建立用户画像提示词`.
- Step 3 inputs must include product info from Step 1 (product/service name, platform context, canonical product page URL) and Step 2 fact evidence.
- Build a persona matrix using behavior-first personas for the product and market scope.
- Persona naming must be behavior archetype based; do not name personas only by background label.
- Use `persona_id` + `behavior archetype` as the only primary persona keys in all Step 3 tables.
- If user specifies a preferred target segment in Step 1, mark it as priority candidate and include it in the matrix comparison.
- Label each persona with common language, language/cultural background, and language/script lock.
- Define one explicit `Language Localization Profile` per selected persona for Step 6 and Step 7 audit.
- Define and write `Target Segment List` (all personas that must be processed in Step 4 to Step 6).
- Do not use `excluded` marker for selected target personas.
- Select core audience with explicit comparison model including:
  - candidate segment size
  - demand intensity (JTBD urgency)
  - conversion readiness / purchase intent strength
- Use a scored or clearly ranked comparison table before final core selection.
- Apply target-list selection rule after scoring:
  - default to top 3 personas unless single-segment processing is explicitly requested by user
  - `core audience` remains priority marker only
- For single-segment processing, still keep full schema with exactly one selected `persona_id`.
- `step3-persona.md` must include `### Language Localization Profile` (table or persona blocks) for all personas in `Target Segment List`.
- Write artifact to `workflow/<run-id>/step3-persona.md`.

### Step 4: Identify Pain / Itch / Delight Points

- Execute only if selected in Step 0.
- Must call template `2) 挖掘目标用户痛点、痒点、爽点的提示词`.
- Analyze all personas in Step 3 `Target Segment List`.
- Output persona-by-persona pain/itch/delight; add cross-persona summary only when multiple personas are selected.
- Add a `Segment Coverage Check` block to confirm all target segments are processed.
- Use Step 3 `persona_id` + `behavior archetype` keys in Step 4 output and coverage check.
- Map each insight to source URL or inference.
- Write artifact to `workflow/<run-id>/step4-pain-itch-delight.md`.

### Step 5: Refine Product Selling Points

- Execute only if selected in Step 0.
- Must call template `3) 挖掘产品卖点的提示词`.
- Use Step 2, Step 3, and Step 4 artifacts.
- Build explicit mapping from each selling point to:
  - Step 2 fact evidence (URL-based)
  - Step 3 target persona
  - Step 4 pain/itch/delight insight
- Filter out all `Restrictions and Fees` items from selling points.
- If restrictions must be disclosed, keep them in separate compliance note only.
- Hard reject rules:
  - discard any selling point without Step 2 fact evidence
  - discard any price/offer selling point without variant binding
- For multi-segment tasks, output persona-grouped selling points with persona language/script lock.
- Every mapping row must reference Step 3 `persona_id` + `behavior archetype`.
- Must cover all personas in Step 3 `Target Segment List`; if a persona has fewer sellable points, still include it in handoff with explicit note.
- `step5-selling-points.md` must include:
  - `### Selling Point Mapping Matrix`
  - `### Non-sellable Restrictions`
  - `### Step6 Handoff`
  - `### Segment Coverage Check`
- Write artifact to `workflow/<run-id>/step5-selling-points.md`.

### Step 6: Draft Platform-Aligned Copy

- Execute only if selected in Step 0.
- Must call template `4) 文案创作提示词`.
- If platform is Xiaohongshu, also call template `5) 小红书种草爆文生成提示词（平台专用）`.
- Must consume `Step5 Handoff` as primary writing input and record adoption/rejection for each handoff item.
- Generate final copy and creative prompts using selected selling points and Step 3 persona language lock.
- Apply Step 3 `Language Localization Profile` to all persona outputs (title, body copy, CTA wording, compliance note wording, image overlays).
- For multi-segment delivery, output separate language-locked copy packages by persona.
- Must generate corresponding copy package for every persona in Step 3 `Target Segment List`.
- Build visual prompts and copy as one integrated asset package; visuals cannot be detached from persona + scenario + claim context.
- Ensure all claims map to official facts.
- Bind every price claim to specific variant context.
- Never combine prices from different variants into one claim.
- If claim is variant-specific, include variant name in copy or in adjacent compliance note.
- Platform visual pack defaults:
  - Xiaohongshu: `4-6` images per persona with fixed slots `cover / pain / process / compare / result / detail(optional)`.
  - Facebook: `3-5` images per persona, tuned for feed conversion flow `hook / scenario / proof / offer / CTA`.
  - Google: `3-5` images per persona, tuned for compliant ad clarity `offer / feature / trust / CTA`.
- For every image slot, include these mandatory fields:
  - `slot`
  - `purpose`
  - `人物`
  - `动作`
  - `场景`
  - `机位`
  - `光线`
  - `构图`
  - `道具`
  - `情绪`
  - `禁止项`
  - `prompt`
  - `negative`
  - `overlay`
  - `claim refs` (if factual text is used)
- Formatted image prompt output lock (mandatory):
  - output image prompts under `### Formatted Image Prompts` as fenced `yaml`
  - one persona block per persona with keys:
    - `persona`
    - `language`
    - `archetype`
    - `slots` (array of slot objects using all mandatory fields above)
  - use concrete, camera-executable descriptions; avoid abstract marketing-only language
  - each slot must focus on one scene and one key action
- Text rendering policy for image generation:
  - base image prompts must request `no readable text in generated image`
  - do not ask model to render price digits, package names, or legal terms inside the image
  - all promotional wording and prices must be delivered via `overlay` only
  - Chinese overlay text should be concise (`<=10` characters preferred)
- Xiaohongshu body copy formatting (copy-paste safe):
  - do not use markdown/list bullets in正文 (`-`, `*`, `•`)
  - use plain-text short paragraphs + line breaks for readability
  - when listing points, use copy-safe Chinese enumeration such as `1）2）3）` or `第一/第二/第三`
  - prefer line-leading labels like `先说结论：` `我会先看这3点：` `最后说重点：`
- Xiaohongshu emoji policy (scene-based, optional but recommended):
  - use emoji as paragraph/section cues, not as markdown bullet substitutes
  - keep density low-to-medium (`3-6` emojis per post by default; `0-1` in title)
  - choose emoji type by scenario:
    - business scenarios (service/efficiency/workflow): functional emojis (`📌✅⚠️💡📞⏱️`)
    - family scenarios (daily use/home/family members/pets): warm reassurance emojis (`🏠👨‍👩‍👧‍👦🧓👶🐶🐱💬`)
    - if the paragraph tone is alert/risk/reminder (in either family or business scenario), use caution-alert emojis sparingly (`🚨⚠️🌙🔔👀`)
    - setup / comparison / buying guide scenarios (both family/business): structure-guide emojis (`1️⃣2️⃣3️⃣`, `📝`, `🔍`, `📊`)
  - avoid playful/over-cute emoji clusters in risk/compliance-heavy scenes (`✨💕😍🥹` etc.)
  - if a paragraph contains compliance/price/condition disclosure, prefer no emoji or one neutral cue only (`⚠️` / `📌`)
- Step 6 pre-completion gate (hard):
  - do not mark Step 6 `completed` unless `### Formatted Image Prompts` exists and is fenced `yaml`
  - every selected persona must have one yaml block with `persona/language/archetype/slots`
  - every slot object must contain all mandatory slot fields listed above
  - for Xiaohongshu, each persona must include slots `cover/pain/process/compare/result` (`detail` optional)
  - base prompt text in each slot must include `no readable text in generated image`
  - for Xiaohongshu body copy, no markdown/list bullets in正文; use copy-paste-safe plain-text formatting
  - if Xiaohongshu正文 uses emoji, emoji type and density must match scenario (family vs business)
- Add one reusable placeholder block for visuals:
  - `[产品] [核心卖点] [关键动作] [痛点] [目标人群画像] [使用场景] [结果状态] [犹豫点参数]`
- `step6-platform-copy.md` must include:
  - `### Step5 Handoff Consumption`
  - `### Platform Asset Package`
  - `### Language Localization Application`
  - `### Visual Creative Pack`
  - `### Formatted Image Prompts`
  - `### Image Prompt Variables`
  - `### Claim Inventory`
  - `### Claim to Variant Binding`
  - `### Segment Coverage in Assets`
  - `### Language Localization Self-Check`
- `### Claim Inventory` is mandatory for Step 7 and must include, at minimum:
  - claim id
  - claim text
  - asset location
  - persona id
  - behavior archetype
  - language/script
  - variant key/name (if applicable)
  - source URL(s)
- Do not replace `persona id` / `behavior archetype` with background-only labels.
- `### Language Localization Application` must record, per persona:
  - Step 3 localization profile used
  - key wording choices adopted
  - wording choices rejected/avoided
  - notable localization tradeoffs (if any)
- `### Language Localization Self-Check` must confirm:
  - script lock match
  - locale/style variant match
  - wording avoid list not violated
  - punctuation/style conventions applied
- Write artifact to `workflow/<run-id>/step6-platform-copy.md`.

### Step 7: Fresh Official Fact-Check and Delivery (Mandatory)

- Always execute Step 7, even if some of Step 1 to Step 6 are skipped.
- Apply current-run official verification retrieval with hybrid freshness:
  - price/promotion/original price/conditions claims -> force-refresh official website in current run
  - non-price feature/spec claims -> cache reuse allowed when `business_info/` cache age is `<= 7` days
  - any cache older than 7 days -> refresh before use
- Enforce `Allowed Fact Domains` from Step 0 for all fresh verification fetches.
- Do not use Step 2 to Step 6 artifacts as final evidence source.
- Determine claim source dynamically:
  - If Step 6 exists and includes claim list/binding, use Step 6 claim list.
  - If Step 6 does not exist or has no claim list, extract claims directly from content under review (user-provided copy, optionally supported by Step 2 claim inventory).
- Build a targeted verification URL set from selected claims and fetch only required URLs.
- Avoid broad site-wide search in Step 7.
- Reject any verification URL outside `Allowed Fact Domains` unless user explicitly requested that domain in Step 0.
- If Step 6 includes visual prompts, audit visual claims and text overlays in the same run.
- Apply source priority rule when evidence conflicts:
  - product canonical page > product interactive variant payload/endpoint > promotion page > legal/other page
- Build `Step7 Fetch Dedup Log` in `step7-fact-check.md`:
  - URL
  - fetched_at
  - purpose
  - allowed domain check (`pass` / `fail`)
  - cache status (`hit` / `miss` / `stale_refresh` / `force_refresh`)
  - cache file path (if used)
  - freshness basis (`forced website refresh` / `cache<=7d` / `cache>7d refreshed`)
  - retry_count
  - retry_reason (if any)
- Within Step 7, do not fetch the same URL repeatedly for the same purpose.
- Retry strategy for transient failures:
  - at most 2 retries for timeout/5xx
  - record retries in `Step7 Fetch Dedup Log`
- Validate each selected claim against current-run official evidence (forced fresh website retrieval for price/promo/conditions; cache<=7d allowed for non-price features/specs).
- Validate language/script consistency against Step 3 persona language lock policy.
- Audit language localization consistency against Step 3 `Language Localization Profile` and Step 6 `Language Localization Self-Check` (audit-only in Step 7; rewrite happens in Step 6).
- For `interactive-variant` pages, re-enter matching variant state for each claim before validation.
- Validate segment coverage consistency: every Step 3 target persona must have corresponding Step 6 asset package.
- Validate visual coverage consistency: every Step 6 visual slot that includes factual wording must map to claim ids and be rechecked against current-run official evidence (price/conditions fresh refresh; non-price may use cache<=7d).
- Write `workflow/<run-id>/step7-fact-check.md` with claim-level table:
  - claim id (must map to Step 6 `Claim Inventory` when available)
  - claim
  - variant key/name
  - variant evidence (UI-state / payload / endpoint and state key)
  - claim source (`step6` / `input-copy` / `step2-inventory`)
  - source priority used
  - language/script check
  - latest official URL
  - fetched_at (with timezone)
  - fresh evidence extract
  - mismatch reason code (`price_conflict` / `condition_missing` / `variant_mismatch` / `language_mismatch` / `not_found`)
  - match status (`verified` / `not found` / `mismatch`)
  - action taken
- Also include `Segment Coverage Audit` table:
  - persona id
  - behavior archetype
  - in step3 target list (`yes/no`)
  - step6 asset package present (`yes/no`)
  - language/script match (`yes/no`)
  - status (`pass` / `fail`)
  - action taken
- `Segment Coverage Audit` must use Step 3 `persona_id` + `behavior archetype` keys.
- Also include `Language Localization Audit` table:
  - persona id
  - behavior archetype
  - target locale/style variant (from Step 3)
  - checked assets/sections
  - script lock check (`pass/fail`)
  - locale wording check (`pass/fail`)
  - punctuation/style check (`pass/fail`)
  - issue summary
  - status (`pass/fail`)
  - action taken
- Step 7 is audit-only for localization; if localization fails, record warning and suggested revision, but do not auto-rewrite Step 6 copy in Step 7.
- If Step 6 contains visual prompts, also include `Visual Prompt Audit` table:
  - visual id / slot
  - persona id
  - language/script check
  - factual text/overlay
  - mapped claim id(s)
  - latest official URL
  - fetched_at
  - status (`verified` / `not found` / `mismatch`)
  - action taken
- If any claim has `not found` / `mismatch`, also include `Conflict Notice` table:
  - claim id (if available)
  - claim
  - conflict type
  - affected output section
  - evidence source A
  - evidence source B (`N/A` if none)
  - recommended handling
  - user-visible warning message
- If `not found` or `mismatch` exists:
  - do not auto-edit Step 6 copy in Step 7
  - keep original generated copy unchanged
  - add explicit conflict/warning notes in Step 7 (including `price_conflict` source URLs and mismatch reason)
  - if user requests revision, revise in a new Step 6 pass and then rerun Step 7
  - delivery may proceed with warning flags when user asked for review/reporting, but unresolved claims must be clearly marked `manual review required`
- Do not auto-rerun Step 7 for content conflicts/mismatches; only retry transient fetch failures (timeout/5xx) within the same Step 7 run.

## Codex Tooling and MCP Contract

- Target Codex execution. Do not use Claude Code specific tool names or assumptions.
- Prefer Codex native retrieval for official pages.
- If MCP is configured, call MCP tools by configured identifiers only.
- Record tool trace in each step artifact:
  - retrieval/write/validation action
  - execution channel (`Codex native` or `MCP`)
  - fallback when MCP is unavailable
- Never fabricate MCP outputs.

## Platform Writing Rules

### Google Ads

- Respect ad format limits; default to `headline <= 30 chars` and `description <= 90 chars` for Latin script when exact setup is unknown.
- Avoid exclamation marks.
- Keep message direct: user intent + verified offer + CTA.
- Visual direction: prioritize compliant product clarity, less lifestyle clutter, and include both square and landscape concepts when needed.

### Facebook Ads

- Prioritize hook, scenario, benefit, and CTA flow.
- Tie each message to specific pain point and verified offer/fact.
- Keep copy and image/video prompts aligned on one scenario and value proposition.
- Visual direction: feed-first social realism; default concept to `4:5` portrait and keep one scene one value proposition.

### Xiaohongshu

- Use natural peer tone with strong "活人感".
- Prefer scene-based storytelling plus practical benefits.
- Enforce title length: `<= 20` Chinese characters unless user explicitly requests otherwise.
- Enforce `<= 400` Chinese characters unless user asks otherwise.
- Body formatting must be copy-paste safe for Xiaohongshu editor:
  - no markdown/list bullets (`-`, `*`, `•`) in正文
  - use paragraph breaks + Chinese enumerators (`1）2）3）` / `第一、第二、第三`)
- Emoji usage is allowed and should be scenario-based:
  - business posts: functional cues only (`📌✅⚠️💡📞⏱️`)
  - family posts: warm home/family cues; if reminder/alert tone is needed, add light alert cues (`🏠👨‍👩‍👧‍👦🧓👶🐶🐱🔔`)
  - alert/risk paragraphs (any scenario): sparse caution-alert cues (`🚨⚠️🌙👀`)
  - avoid dense cute-style emoji in risk/compliance-heavy copy
- Always apply template `5) 小红书种草爆文生成提示词（平台专用）`.
- Visual direction: smartphone candid look, low-ad feel, default `3:4` portrait, and use `cover/pain/process/compare/result` slot logic.

## Output Structure

- Request Summary
- Plan Status (Step 0 to Step 7)
- Step Selection Decision Matrix Result
- Mandatory Artifact Paths (`step0-plan.md`, `step7-fact-check.md`)
- Executed Optional Step Artifact Paths (from Step 0 selection)
- Skipped Optional Steps and Reasons
- Audience Segment and Language Lock
- Target Segment List
- Source Facts (Official URLs)
- Fetch Dedup Log (from Step 2)
- Variant Price Matrix (if interactive page)
- Restrictions and Fees (Compliance Note)
- Persona Summary (Core + Segment Comparison)
- Pain / Itch / Delight Summary
- Segment Coverage Check (Step 4/5)
- Key Selling Points
- Step5 Handoff Consumption
- Final Copy
- Claim Inventory (for Step 7)
- Claim to Variant Binding
- Segment Coverage in Assets
- Visual Creative Pack
- Formatted Image Prompts (YAML)
- Image Prompt Variables
- Image Generation Prompts
- Video Generation Prompts
- Step7 Fetch Dedup Log
- Fact Check (from Step 7 current-run official comparison with hybrid freshness policy)
- Segment Coverage Audit (Step 7)
- Language Localization Audit (Step 7)
- Visual Prompt Audit (Step 7, if Step 6 has visual prompts)
- Mismatch Reason Summary
- Unverified or Removed Claims

## References

- Use `references/analysis-prompts.md` for template execution guidance.
- Use Step 7 current-run official evidence as final verification source (price/promo/conditions force refresh; non-price claims may use cache<=7d).
- Use `references/business-url-registry.json` + `scripts/business_info_cache.py` for locked business URL mapping and `business_info/` cache management.
- Optional local schema check tool: `scripts/validate_artifacts.sh workflow/<run-id>`.
