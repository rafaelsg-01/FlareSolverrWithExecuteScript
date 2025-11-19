#!/bin/bash
cd content-proxy-web || true

echo "Parando o container content-proxy-web-01..."

docker stop content-proxy-web-01

echo "Container parado."
