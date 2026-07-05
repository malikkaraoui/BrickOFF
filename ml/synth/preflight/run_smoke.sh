#!/bin/zsh
# Smoke-test avec reprise sur crash : relance Blender tant que smoke_done.flag absent.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
MAX_RUNS=15
rm -f "$DIR/out/smoke_done.flag"
for i in $(seq 1 $MAX_RUNS); do
  echo "=== run $i ==="
  "$BLENDER" --background --python "$DIR/01_smoke.py" 2>&1 | grep -Ev "^(Fra:|INFO )" | tail -5
  if [ -f "$DIR/out/smoke_done.flag" ]; then
    echo "=== smoke-test terminé (run $i) ==="
    exit 0
  fi
done
echo "=== ABANDON après $MAX_RUNS runs ==="
exit 1
