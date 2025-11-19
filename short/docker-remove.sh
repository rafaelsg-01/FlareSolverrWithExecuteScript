#!/bin/bash
cd content-proxy-web || true

echo "Removendo container content-proxy-web-01..."

docker rm content-proxy-web-01

echo "Container removido."
