#!/bin/bash
cd content-proxy-web || true

echo "Iniciando o container content-proxy-web-01..."

docker run -d \
    --name content-proxy-web-01 \
    -p 8191:8191 \
    --env-file ./.env \
    -e LOG_LEVEL=info \
    --restart unless-stopped \
    build-content-proxy-web

echo "Proxy Web iniciado em http://127.0.0.1:80 (acessível via Cloudflare/domínio)."
