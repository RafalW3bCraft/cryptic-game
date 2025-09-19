#!/usr/bin/env bash
# scripts/session-end.sh
# Usage: sudo ./scripts/session-end.sh <operator_handle> "optional note"
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo) to remove iptables rules and stop the lab."
  exit 2
fi

OP=${1:-"unknown"}
NOTE=${2:-""}
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESS_DIR="sessions"
mkdir -p "${SESS_DIR}"

# Find the most recent session file for this operator (best-effort)
LATEST=$(ls -1t ${SESS_DIR}/session-*.yaml 2>/dev/null | head -n1 || true)
if [ -n "$LATEST" ]; then
  echo "end: $TS" >> "$LATEST"
  echo "note: $NOTE" >> "$LATEST"
  echo "session file updated: $LATEST"
else
  # create a new session-end file
  echo "operator: $OP" > "${SESS_DIR}/session-end-${TS}.yaml"
  echo "end: $TS" >> "${SESS_DIR}/session-end-${TS}.yaml"
  echo "note: $NOTE" >> "${SESS_DIR}/session-end-${TS}.yaml"
  echo "created: ${SESS_DIR}/session-end-${TS}.yaml"
fi

# Remove the DOCKER-USER rule with TheFool marker (if present)
# We search for a rule containing the comment "TheFool lab egress block"
RULE_LINE=$(iptables -L DOCKER-USER --line-numbers 2>/dev/null | grep -n "TheFool lab egress block" || true)
if [ -n "$RULE_LINE" ]; then
  # extract the line number (format: N: <rest>)
  LINE_NUM=$(echo "$RULE_LINE" | head -n1 | cut -d: -f1)
  sudo iptables -D DOCKER-USER $LINE_NUM || true
  echo "Removed DOCKER-USER rule at line $LINE_NUM"
else
  echo "No TheFool DOCKER-USER rule found — nothing to remove."
fi

# Stop the lab gracefully
docker compose down || true

echo "Lab stopped and session closed at $TS"
