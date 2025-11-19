#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Hard-reset container content-proxy-web-01..."

read -r -p "HARD-RESET. Tem certeza? digite 'yes' para continuar: " response
if [[ "$response" != "yes" ]]; then
    echo "Operação cancelada."
    exit 0
fi

bash ./short/docker-stop.sh
bash ./short/docker-remove.sh
bash ./short/docker-git-pull.sh
bash ./short/docker-build.sh
bash ./short/docker-run.sh

echo "Hard-reset container."
