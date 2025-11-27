#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Run container content-proxy-web-01..."

docker run -d \
    --name content-proxy-web-01 \
    --network caddy-net \
    --env-file ./.env \
    -e LOG_LEVEL=info \
    --memory="450m" \
    --memory-swap="4450m" \
    --memory-reservation="350m" \
    --memory-swappiness=100 \
    --shm-size="128m" \
    --oom-kill-disable=false \
    --restart=always \
    build-content-proxy-web

echo "Run container."

echo "Proxy Web iniciado em http://127.0.0.1:8191 (acessível via Cloudflare/domínio)."
