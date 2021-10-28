#!/bin/bash

# limit server to max requests. It will be restarted by kubernetes
# add some random jitter so every server doesn't restart at once
max_requests=$((10000 + RANDOM/10))  # RANDOM is in range (0,32k)
echo "starting uvicorn with max-requests $max_requests"

exec uvicorn \
    --workers 1 \
    --limit-max-requests $max_requests \
    --host 0.0.0.0 \
    --port 3000 \
    titiler.application.main:app
