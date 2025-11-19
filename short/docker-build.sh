#!/bin/bash
cd content-proxy-web || true

echo "Criando imagem Docker build-content-proxy-web:latest..."

docker build -t build-content-proxy-web:latest .

echo "Imagem Docker criada."
