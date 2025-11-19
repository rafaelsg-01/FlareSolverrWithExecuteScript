#!/bin/bash
cd $HOME/content-proxy-web || true

# Dar permissão de execução:
cd $HOME/content-proxy-web && chmod +x menu.sh && cd $HOME/content-proxy-web/short && chmod +x *.sh

# Caminho para os scripts
SCRIPTS_DIR="./short"

while true; do
    echo ""
    echo "===== MENU PROXY WEB ====="
    echo "Escolha uma opção:"
    echo "1) Git Pull (Update Local)"
    echo "2) Docker Build"
    echo "3) Docker Run"
    echo "4) Docker Stop"
    echo "5) Docker Start"
    echo "6) Docker Remove"
    echo "7) Docker Logs"
    echo "8) Docker Soft Reset"
    echo "9) Docker Hard Reset"
    echo "0) Sair"
    echo "====================="
    read -p "Digite o número da opção: " opcao

    case $opcao in
        1) bash "$SCRIPTS_DIR/docker-git-pull.sh" ;;
        2) bash "$SCRIPTS_DIR/docker-build.sh" ;;
        3) bash "$SCRIPTS_DIR/docker-run.sh" ;;
        4) bash "$SCRIPTS_DIR/docker-stop.sh" ;;
        5) bash "$SCRIPTS_DIR/docker-start.sh" ;;
        6) bash "$SCRIPTS_DIR/docker-remove.sh" ;;
        7) bash "$SCRIPTS_DIR/docker-logs.sh" ;;
        8) bash "$SCRIPTS_DIR/docker-soft-reset.sh" ;;
        9) bash "$SCRIPTS_DIR/docker-hard-reset.sh" ;;
        0) echo "Saindo..."; exit ;;
        *) echo "Opção inválida!";;
    esac
done
