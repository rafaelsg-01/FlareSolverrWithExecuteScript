#!/bin/bash
cd content-proxy-web || true

echo "Log do container content-proxy-web-01:"

docker logs -f content-proxy-web-01
