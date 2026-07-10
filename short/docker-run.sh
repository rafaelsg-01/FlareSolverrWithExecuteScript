#!/bin/bash
cd $HOME/content-proxy-web || true

# Le so o SERVER_TYPE do .env (sem sourcear o arquivo inteiro, que tem URLs com # etc)
SERVER_TYPE=$(grep -E '^SERVER_TYPE=' ./.env 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"\r' | xargs)
[ -z "$SERVER_TYPE" ] && SERVER_TYPE="google-cloud"

echo "Run container content-proxy-web-01... (SERVER_TYPE=$SERVER_TYPE)"

if [ "$SERVER_TYPE" = "servidor-caseiro" ]; then
    # ---------- SERVIDOR CASEIRO (notebook) ----------
    docker run -d \
        --name content-proxy-web-01 \
        --network flare-net \
        --env-file ./.env \
        -p 8191:8191 \
        -e LOG_LEVEL=debug \
        -e LOG_HTML=true \
        -e TZ=America/Sao_Paulo \
        --memory="2g" \
        --memory-swap="4g" \
        --memory-reservation="1g" \
        --memory-swappiness=60 \
        --shm-size="512m" \
        --restart unless-stopped \
        build-content-proxy-web
else
    # ---------- GOOGLE CLOUD (VM free) ----------
    docker run -d \
        --name content-proxy-web-01 \
        --network caddy-net \
        --env-file ./.env \
        -e LOG_LEVEL=debug \
        -e LOG_HTML=true \
        --memory="500m" \
        --memory-swap="4500m" \
        --memory-reservation="250m" \
        --memory-swappiness=100 \
        --shm-size="128m" \
        --oom-kill-disable=false \
        build-content-proxy-web
fi

echo "Run container."

echo "Proxy Web iniciado em http://127.0.0.1:8191 (acessível via Cloudflare/domínio)."
