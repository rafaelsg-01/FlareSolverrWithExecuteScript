# send-request.ps1
# Manda um request.get para o servidor local (que ja deve estar no ar via run-local.ps1).
# Uma janela do Chrome vai abrir e voce ve o Cloudflare sendo resolvido.
#
# Uso:
#   .\send-request.ps1                          -> usa a URL padrao (custom.css)
#   .\send-request.ps1 "https://redecanais.uk/templates/echo/css/style.css"   -> testa OUTRA url
#   .\send-request.ps1 "https://redecanais.uk/" -> testa a home
#
# Dica: use este script para caçar uma pagina "leve" que exista e nao seja bloqueada,
# para estacionar o FlareSolverr nela.

param(
    [string]$Url = "https://redecanais.uk/templates/echo/css/custom.css#_execScript_setHeadersRedeCanais"
)

$body = @{
    cmd        = "request.get"
    url        = $Url
    maxTimeout = 90000
} | ConvertTo-Json

Write-Host "Enviando request.get para: $Url" -ForegroundColor Cyan
Write-Host "(uma janela do Chrome vai abrir; aguarde ate ~1-2 min)" -ForegroundColor DarkGray

try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8191/v1" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 120
    $title = ([regex]::Match($res.solution.response, '<title>(.*?)</title>')).Groups[1].Value
    $len   = $res.solution.response.Length
    Write-Host ""
    Write-Host "status  : $($res.status)"
    Write-Host "message : $($res.message)"
    Write-Host "title   : $title"
    Write-Host "url final: $($res.solution.url)"
    Write-Host "tamanho : $len chars"
    if ($res.solution.response -match 'you have been blocked') {
        Write-Host "==> BLOQUEADO pela Cloudflare (erro 1020 / regra WAF)" -ForegroundColor Red
    } elseif ($title -match 'moment|momento') {
        Write-Host "==> Ainda na tela de desafio (nao resolveu)" -ForegroundColor Yellow
    } elseif ($len -lt 60) {
        Write-Host "==> Pagina vazia/minima (pode nao existir mais)" -ForegroundColor Yellow
    } else {
        Write-Host "==> OK: chegou numa pagina real" -ForegroundColor Green
    }
} catch {
    Write-Host "ERRO na chamada: $_" -ForegroundColor Red
}
