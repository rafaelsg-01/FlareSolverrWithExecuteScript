#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Logs do container content-proxy-web-01..."

docker logs -f content-proxy-web-01
