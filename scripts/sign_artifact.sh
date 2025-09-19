#!/usr/bin/env bash
# scripts/sign_artifact.sh <path-to-file> [gpg-key]
if [ -z "$1" ]; then
  echo "Usage: $0 <file> [gpg-key]"
  exit 2
fi
FILE="$1"
KEY="$2"
if [ -n "$KEY" ]; then
  gpg --local-user "$KEY" --armor --detach-sign "$FILE"
else
  gpg --armor --detach-sign "$FILE"
fi
echo "Signed: $FILE.asc"
