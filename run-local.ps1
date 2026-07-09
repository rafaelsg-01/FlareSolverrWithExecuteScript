# run-local.ps1
# Sobe o FlareSolverr (proxy-web) localmente no Windows, igual roda na VM,
# mas com o navegador VISIVEL para diagnostico.
#
# Uso:
#   .\run-local.ps1              -> janela visivel, SEM auto-request (recomendado p/ ver o desafio)
#   .\run-local.ps1 -Reproduce   -> igual a VM: headless + auto request do INITIAL_URL no boot
#
# Depois de subir, em OUTRO terminal, mande o request (veja send-request.ps1 ou o README abaixo).

param(
    [switch]$Reproduce
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "venv nao encontrado em $python. Rode primeiro: py -3.12 -m venv .venv ; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

$env:PORT = "8191"
$env:TOKEN_PROXY_WEB = ""   # sem token para simplificar o teste local
$env:LANG = "en-US"         # faz a Cloudflare servir o desafio em ingles (deteccao por titulo funciona)

if ($Reproduce) {
    # Modo "igual a VM": headless + dispara sessao/request automaticamente no startup.
    # A janela do Chrome fica INVISIVEL (maxOptimization forca --headless=new).
    $env:HEADLESS = "true"
    $env:LOG_LEVEL = "info"
    $env:INITIAL_URL = "https://redecanais.uk/templates/echo/css/custom.css#_execScript_setHeadersRedeCanais"
    Write-Host "== Modo REPRODUCE (headless, auto-request igual a VM) ==" -ForegroundColor Yellow
} else {
    # Modo diagnostico: janela VISIVEL, sem auto-request. Voce manda o request na mao.
    $env:HEADLESS = "false"
    $env:LOG_LEVEL = "debug"
    $env:INITIAL_URL = ""
    Write-Host "== Modo DIAGNOSTICO (navegador visivel, sem auto-request) ==" -ForegroundColor Green
    Write-Host "Servidor em http://127.0.0.1:8191  |  mande o request em outro terminal (veja send-request.ps1)" -ForegroundColor Green
}

Set-Location (Join-Path $root "src")
& $python -u flaresolverr.py
