#!/usr/bin/env bash
set -euo pipefail
# Simple probe script to test SportMonks endpoints and versions with the current API key.
# Usage:
#   export SPORTMONKS_API_KEY="your_key"
#   bash /workspaces/analise-ch-boot/sportmonks_probe.sh

OUT=/tmp/sportmonks_probe.txt
echo "SportMonks probe started at $(date)" > "$OUT"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

load_env_file() {
  local file="$1"
  if [ -f "$file" ]; then
    # shellcheck disable=SC1090
    set -a && source "$file" && set +a
    echo "Loaded env vars from $file" >> "$OUT"
    return 0
  fi
  return 1
}

if [ -z "${SPORTMONKS_API_KEY:-}" ]; then
  load_env_file "$SCRIPT_DIR/.env" || load_env_file "$SCRIPT_DIR/../.env" || true
fi

if [ -z "${SPORTMONKS_API_KEY:-}" ]; then
  echo "ERROR: SPORTMONKS_API_KEY not set. Export it first or add to .env" | tee -a "$OUT"
  exit 2
fi

run_curl(){
  local label="$1"; shift
  echo "\n--- [$label] ---" | tee -a "$OUT"
  echo "Command: curl -i $*" | tee -a "$OUT"
  echo "--- Response ---" >> "$OUT"
  curl -i "$@" 2>&1 | tee -a "$OUT"
  echo "--- End $label ---\n" | tee -a "$OUT"
}

KEY="$SPORTMONKS_API_KEY"

# 1) Root host check
run_curl "root-soccer-v2" "https://soccer.sportmonks.com/api/v2.0/?api_token=${KEY}"

# 2) fixtures on soccer.sportmonks.com v2
run_curl "fixtures-soccer-v2" "https://soccer.sportmonks.com/api/v2.0/fixtures?api_token=${KEY}&league_id=71&per_page=1"

# 3) fixtures on api.sportmonks.com v2
run_curl "fixtures-api-v2" "https://api.sportmonks.com/v2.0/fixtures?api_token=${KEY}&league_id=71&per_page=1"

# 4) fixtures v3 variations
run_curl "fixtures-api-v3" "https://api.sportmonks.com/v3/football/fixtures?api_token=${KEY}&per_page=1"
run_curl "fixtures-soccer-v3" "https://soccer.sportmonks.com/api/v3/football/fixtures?api_token=${KEY}&per_page=1"

# 5) teams endpoint (v2)
run_curl "teams-soccer-v2" "https://soccer.sportmonks.com/api/v2.0/teams?api_token=${KEY}&per_page=1"

echo "Probe complete. Output saved to $OUT"
echo "To view: less $OUT or sed -n '1,200p' $OUT"
