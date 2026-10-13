#!/usr/bin/env bash
# Open Design -> image generation via the media API.
# Task 1 probe: endpoint/auth/poll mechanics VERIFIED (202 + taskId, /wait returns status).
# NOTE: OpenAI Image key in Open Design currently has no credits (429 insufficient_quota).
# Alternate configured providers: grok ('grok-imagine-image'),
#   nanobanana/Google ('gemini-3.1-flash-image-preview'),
#   openrouter ('openrouter/google/gemini-2.5-flash-image').
#
# Usage:
#   export OD_BASE_URL='https://open-design.<reverse-dns>'   # no default; do not commit host
#   export OD_API_TOKEN='<64-char token from od-deploy/.env>'
#   export OD_PROJECT_ID='brand-letta-stack-7f0f25'
#   bash scripts/od_generate.sh 'a beautiful watch dial' gpt-image-1 output.png
set -euo pipefail

: "${OD_BASE_URL:?set OD_BASE_URL}"
: "${OD_API_TOKEN:?set OD_API_TOKEN}"
: "${OD_PROJECT_ID:?set OD_PROJECT_ID}"

PROMPT="${1:?usage: $0 '<prompt>' [model] [output.png]}"
MODEL="${2:-gpt-image-1}"
OUTPUT="${3:-generated.png}"

# Origin header matching the service host is required to pass the same-origin gate.
AUTH=(-u "open-design:${OD_API_TOKEN}" -H "Origin: ${OD_BASE_URL}")

json_get() {
  local key="$1"
  python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("'"$key"'", ""))' 2>/dev/null || true
}

esc_json() {
  python3 -c 'import sys,json; print(json.dumps(sys.argv[1]))' "$1"
}

echo "== generate (${MODEL}) -> ${OUTPUT}"
BODY="$(python3 -c 'import sys,json; print(json.dumps({"surface":"image","model":sys.argv[1],"prompt":sys.argv[2],"output":sys.argv[3]}))' "$MODEL" "$PROMPT" "$OUTPUT")"
resp=$(curl -sk -m 120 "${AUTH[@]}" -X POST "${OD_BASE_URL}/api/projects/${OD_PROJECT_ID}/media/generate" \
  -H 'Content-Type: application/json' \
  -d "$BODY")
echo "$resp"

task=$(printf '%s' "$resp" | json_get taskId)
[ -z "$task" ] && { echo "ERROR: no taskId in response"; exit 1; }

echo "== poll task ${task}"
status="running"
for i in $(seq 1 60); do
  st=$(curl -sk -m 40 "${AUTH[@]}" -X POST "${OD_BASE_URL}/api/media/tasks/${task}/wait" \
    -H 'Content-Type: application/json' -d '{"timeoutMs":25000}')
  status=$(printf '%s' "$st" | json_get status)
  echo "  [$i] status=${status}"
  if [ "$status" = done ]; then break; fi
  if [ "$status" = failed ] || [ "$status" = interrupted ]; then echo "$st"; exit 1; fi
  sleep 2
done

if [ "$status" != done ]; then echo "ERROR: task did not finish (${status})"; exit 1; fi

echo "== download ${OUTPUT}"
curl -sk -m 60 "${AUTH[@]}" -o "${OUTPUT}" "${OD_BASE_URL}/api/projects/${OD_PROJECT_ID}/raw/${OUTPUT}"
file "${OUTPUT}"
