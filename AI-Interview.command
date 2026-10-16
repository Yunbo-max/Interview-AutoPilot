#!/bin/bash
# Finder: double-click this file in the unpacked project; or run with Bash from a local Agent.
set -u
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || exit 2
cd "$ROOT" || exit 2
/bin/bash "$ROOT/skills/ai-interview/scripts/one-click-mac.sh" "$@"
result=$?
if (( result != 0 )) && [[ -t 0 ]]; then
  echo ''
  echo "Setup could not complete (exit $result). See the message above."
  echo 'Press Return to close this Terminal window.'
  read -r _
fi
exit "$result"
