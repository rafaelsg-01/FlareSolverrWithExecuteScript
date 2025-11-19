#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Remove container content-proxy-web-01..."

docker rm content-proxy-web-01

echo "Remove container."
