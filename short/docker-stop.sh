#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Stop container content-proxy-web-01..."

docker stop content-proxy-web-01

echo "Stop container."