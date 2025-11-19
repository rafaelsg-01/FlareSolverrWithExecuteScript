#!/bin/bash
cd content-proxy-web || true

echo "Reiniciando o container content-proxy-web-01..."

bash ./short/docker-stop.sh
bash ./short/docker-remove.sh
bash ./short/docker-build.sh
bash ./short/docker-run.sh

echo "Container reiniciado."
