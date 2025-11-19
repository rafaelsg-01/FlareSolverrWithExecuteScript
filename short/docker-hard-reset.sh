#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Hard-reset container content-proxy-web-01..."

bash ./short/docker-stop.sh
bash ./short/docker-remove.sh
bash ./short/docker-git-reset-hard.sh
bash ./short/docker-build.sh
bash ./short/docker-run.sh

echo "Hard-reset container."
