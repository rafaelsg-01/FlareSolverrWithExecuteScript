#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Build imagem Docker build-content-proxy-web:latest..."

docker build -t build-content-proxy-web:latest .

echo "Build imagem Docker."
