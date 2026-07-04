#!/usr/bin/env bash
# BrickOFF — build + tests unitaires sur simulateur iOS (CH-4 jalon 4.4).
#
# Usage : ios/scripts/build_test.sh
#   (rejouable depuis n'importe quel cwd ; utilisé tel quel par la CI GitHub Actions)
#
# Destination :
#   - par défaut : simulateur "iPhone 17" (parc local + runners macos-26) ;
#     surchargable via BRICKOFF_SIM_DEVICE.
#   - fallback documenté : si ce simulateur n'existe pas sur la machine
#     (ex. runner CI avec un autre SDK iOS), on prend le premier iPhone
#     disponible listé par `xcrun simctl list devices available`.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> xcodegen generate"
xcodegen generate

SCHEME="BrickOFF"
PREFERRED_DEVICE="${BRICKOFF_SIM_DEVICE:-iPhone 17}"

if xcrun simctl list devices available | grep -qE "^[[:space:]]+${PREFERRED_DEVICE} \("; then
  DEVICE="$PREFERRED_DEVICE"
else
  DEVICE="$(xcrun simctl list devices available \
    | sed -nE 's/^[[:space:]]+(iPhone[^(]*[^ (])[[:space:]]*\(.*/\1/p' \
    | head -n 1)"
  if [[ -z "$DEVICE" ]]; then
    echo "error: aucun simulateur iPhone disponible sur cette machine" >&2
    exit 1
  fi
  echo "warning: simulateur '${PREFERRED_DEVICE}' introuvable — fallback sur '${DEVICE}'" >&2
fi

echo "==> xcodebuild build test (destination : ${DEVICE})"
xcodebuild build test \
  -scheme "$SCHEME" \
  -destination "platform=iOS Simulator,name=${DEVICE}"
