#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <workflow-run-dir>" >&2
  exit 1
fi

run_dir="$1"

if [ ! -d "$run_dir" ]; then
  echo "ERROR: run dir not found: $run_dir" >&2
  exit 1
fi

fails=0

require_file() {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "FAIL missing file: $f"
    fails=$((fails + 1))
  else
    echo "OK   file exists: $f"
  fi
}

require_pattern() {
  local f="$1"
  local p="$2"
  local msg="$3"
  if [ ! -f "$f" ]; then
    return
  fi
  if rg -q --fixed-strings "$p" "$f"; then
    echo "OK   $msg"
  else
    echo "FAIL $msg"
    fails=$((fails + 1))
  fi
}

check_table_header_contains() {
  local f="$1"
  local anchor="$2"
  local col1="$3"
  local col2="$4"
  local msg="$5"
  if [ ! -f "$f" ]; then
    return
  fi

  local header
  header=$(awk -v anchor="$anchor" '
    $0 ~ anchor {found=1; next}
    found && $0 ~ /^\|/ {print; exit}
  ' "$f")

  if [ -z "$header" ]; then
    echo "FAIL $msg (header not found)"
    fails=$((fails + 1))
    return
  fi

  if [[ "$header" == *"$col1"* && "$header" == *"$col2"* ]]; then
    echo "OK   $msg"
  else
    echo "FAIL $msg"
    echo "     header: $header"
    fails=$((fails + 1))
  fi
}

step0="$run_dir/step0-plan.md"
step3="$run_dir/step3-persona.md"
step4="$run_dir/step4-pain-itch-delight.md"
step5="$run_dir/step5-selling-points.md"
step6="$run_dir/step6-platform-copy.md"
step7="$run_dir/step7-fact-check.md"

# Mandatory files for all runs.
require_file "$step0"
require_file "$step7"

# Step 3 schema checks (if selected).
check_table_header_contains "$step3" "^### Target Segment List" "persona_id" "behavior archetype" "Step3 Target Segment List has persona keys"
check_table_header_contains "$step3" "^### Persona Candidate Matrix" "persona_id" "behavior archetype" "Step3 Persona Candidate Matrix has persona keys"
check_table_header_contains "$step3" "^### Core Audience Scoring" "persona_id" "behavior archetype" "Step3 Core Audience Scoring has persona keys"

# Step 4 schema checks (if selected).
check_table_header_contains "$step4" "^## Output" "persona_id" "behavior archetype" "Step4 output table has persona keys"
check_table_header_contains "$step4" "^### Segment Coverage Check" "persona_id" "behavior archetype" "Step4 Segment Coverage Check has persona keys"

# Step 5 schema checks (if selected).
check_table_header_contains "$step5" "^### Selling Point Mapping Matrix" "persona_id" "behavior archetype" "Step5 mapping matrix has persona keys"
check_table_header_contains "$step5" "^### Step6 Handoff" "persona_id" "behavior archetype" "Step5 handoff table has persona keys"
check_table_header_contains "$step5" "^### Segment Coverage Check" "persona_id" "behavior archetype" "Step5 coverage table has persona keys"

# Step 6 schema checks (if selected).
check_table_header_contains "$step6" "^### Step5 Handoff Consumption" "handoff_id" "persona_id" "Step6 handoff consumption links handoff to persona"
check_table_header_contains "$step6" "^### Claim Inventory" "persona_id" "behavior archetype" "Step6 claim inventory has persona keys"
check_table_header_contains "$step6" "^### Segment Coverage in Assets" "persona_id" "behavior archetype" "Step6 segment coverage has persona keys"

# Step 7 schema checks.
check_table_header_contains "$step7" "^### Fact Check" "claim id" "language/script check" "Step7 fact-check table includes language/script check"
check_table_header_contains "$step7" "^### Segment Coverage Audit" "persona_id" "behavior archetype" "Step7 coverage audit has persona keys"

# Global drift guard.
require_pattern "$step3" "persona_id" "Step3 includes persona_id"
require_pattern "$step6" "persona_id" "Step6 includes persona_id"
require_pattern "$step7" "persona_id" "Step7 includes persona_id"

if [ "$fails" -eq 0 ]; then
  echo "PASS schema checks"
  exit 0
fi

echo "FAILED checks: $fails"
exit 2
