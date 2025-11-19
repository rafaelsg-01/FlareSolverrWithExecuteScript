#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Soft-reset container content-proxy-web-01..."

bash ./short/docker-stop.sh

# conta 5 segundos
for i in {5..1}
do
   echo "Religando em 5/$i segundos..."
   sleep 1
done

bash ./short/docker-start.sh

echo "Soft-reset container."
