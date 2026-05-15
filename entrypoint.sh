#!/bin/sh
set -e

# start opencode serve in background
opencode serve --hostname 0.0.0.0 --port 4096 &
echo "Waiting for opencode serve to be ready..."

for i in $(seq 1 30); do
  if curl -sf --max-time 2 http://127.0.0.1:4096/session/status > /dev/null 2>&1; then
    echo "opencode serve is ready"
    break
  fi
  sleep 1
done

# start adapter
exec python /app/adapter.py
