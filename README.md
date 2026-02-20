# italkbb-ads-writer

Skill package for generating iTalkBB ad copy and creative prompts with strict fact verification workflow.

## Included Files

```text
italkbb-ads-writer/
├── SKILL.md
├── agents/openai.yaml
├── references/analysis-prompts.md
└── scripts/validate_artifacts.sh
```

## What It Does

- Runs plan-first workflow (`Step 0 -> Step 7`) for ad writing.
- Supports Google Ads, Facebook Ads, and Xiaohongshu.
- Enforces official-site fact extraction and fresh Step 7 verification.
- Supports interactive variant pricing pages with claim-to-variant binding.
- Includes schema validator script for workflow artifacts.

## Quick Usage

Run artifact schema checks:

```bash
bash scripts/validate_artifacts.sh workflow/<run-id>
```

## Publish

```bash
git init
git add .
git commit -m "Initial release: italkbb-ads-writer"
gh repo create italkbb-ads-writer --public --source=. --remote=origin --push
```

