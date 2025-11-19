#!/bin/bash

# Caminho para os scripts
SCRIPTS_DIR="./short"

while true; do
    clear
    echo "===== MENU PROXY WEB ====="
    echo "Escolha uma opção:"
    echo "1) Docker Build"
    echo "2) Docker Run"
    echo "3) Docker Stop"
    echo "4) Docker Remove"
    echo "5) Docker Logs"
    echo "6) Docker Restart"
    echo "0) Sair"
    echo "====================="
    read -p "Digite o número da opção: " opcao

    case $opcao in
        1) bash $SCRIPTS_DIR/docker-build.sh ;;
        2) bash $SCRIPTS_DIR/docker-run.sh ;;
        3) bash $SCRIPTS_DIR/docker-stop.sh ;;
        4) bash $SCRIPTS_DIR/docker-remove.sh ;;
        5) bash $SCRIPTS_DIR/docker-logs.sh ;;
        6) bash $SCRIPTS_DIR/docker-restart.sh ;;
        0) echo "Saindo..."; exit ;;
        *) echo "Opção inválida!";;
    esac

    echo ""
    read -p "Pressione Enter para continuar..."
done
