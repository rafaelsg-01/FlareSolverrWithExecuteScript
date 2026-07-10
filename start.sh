#!/bin/sh
# Entrypoint do container: decide se liga o proxy (baseado no SERVER_TYPE + PROXY_ENABLED_*)
# e depois sobe o FlareSolverr.

# Descobre se o proxy deve ficar ligado nesta maquina
PROXY_ON=false
if [ "$SERVER_TYPE" = "google-cloud" ]; then
  PROXY_ON="$PROXY_ENABLED_GOOGLE"
elif [ "$SERVER_TYPE" = "servidor-caseiro" ]; then
  PROXY_ON="$PROXY_ENABLED_CASEIRO"
fi

if [ "$PROXY_ON" = "true" ] && [ -n "$UPSTREAM_HOST" ]; then
  echo "[start] Proxy LIGADO ($SERVER_TYPE) -> forwarder $UPSTREAM_HOST:$UPSTREAM_PORT (listen 127.0.0.1:${FORWARD_LISTEN_PORT:-8898})"
  python -u /app/proxy_forwarder.py &
  # da um tempinho pro forwarder abrir a porta antes do Chrome tentar usar
  sleep 1
else
  echo "[start] Proxy DESLIGADO ($SERVER_TYPE) -> conexao direta (sem proxy)"
  # garante que o FlareSolverr NAO tente usar o forwarder
  unset PROXY_URL
fi

exec python -u /app/flaresolverr.py
