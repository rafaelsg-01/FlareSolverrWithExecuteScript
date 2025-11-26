#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Run container content-proxy-web-01..."

docker run -d \
    --name content-proxy-web-01 \
    --network caddy-net \
    --env-file ./.env \
    -e LOG_LEVEL=info \
    --memory="100m" \
    --memory-swap="900m" \
    --restart unless-stopped \
    build-content-proxy-web

echo "Run container."

echo "Proxy Web iniciado em http://127.0.0.1:8191 (acessível via Cloudflare/domínio)."
