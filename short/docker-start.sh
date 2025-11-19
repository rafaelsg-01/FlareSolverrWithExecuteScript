#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Start container content-proxy-web-01..."

docker start content-proxy-web-01

echo "Start container."