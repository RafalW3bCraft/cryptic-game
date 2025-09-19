#!/usr/bin/env bash
# Usage: sudo ./scripts/run-session.sh <operator_handle> "short goal"
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo) to apply iptables preflight and start the lab."
  exit 2
fi

OP=${1:-"unknown"}
GOAL=${2:-"ad-hoc"}
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
mkdir -p sessions
echo "operator: $OP" > "sessions/session-${TS}.yaml"
echo "start: $TS" >> "sessions/session-${TS}.yaml"
echo "goal: $GOAL" >> "sessions/session-${TS}.yaml"

# apply preflight
./scripts/preflight.sh

# start lab
docker compose up -d --build

echo "Started lab session saved to sessions/session-${TS}.yaml"
