# see-page.ps1
# Pede ao FlareSolverr o HTML que o navegador esta vendo + um PRINT (screenshot)
# e salva os dois em arquivos, abrindo automaticamente pra voce ver.
#
# Precisa do servidor local no ar (run-local.ps1).
#
# Uso:
#   .\see-page.ps1
#   .\see-page.ps1 "https://redecanais.uk/robots.txt"

param(
    [string]$Url = "https://redecanais.uk/templates/echo/css/custom.css#_execScript_setHeadersRedeCanais"
)

$body = @{
    cmd              = "request.get"
    url              = $Url
    maxTimeout       = 90000
    returnScreenshot = $true
} | ConvertTo-Json

Write-Host "Pedindo pagina: $Url" -ForegroundColor Cyan
Write-Host "(janela do Chrome vai abrir; aguarde)" -ForegroundColor DarkGray

$res = Invoke-RestMethod -Uri "http://127.0.0.1:8191/v1" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 120

$html = [string]$res.solution.response
$title = ([regex]::Match($html, '<title>(.*?)</title>')).Groups[1].Value
Write-Host ""
Write-Host "status  : $($res.status)"
Write-Host "message : $($res.message)"
Write-Host "title   : $title"
Write-Host "url final: $($res.solution.url)"
Write-Host "tamanho : $($html.Length) chars"

# salva o HTML
$htmlPath = Join-Path $PSScriptRoot "pagina-vista.html"
[IO.File]::WriteAllText($htmlPath, $html, [Text.Encoding]::UTF8)
Write-Host "HTML salvo em: $htmlPath" -ForegroundColor Green

# salva o screenshot (o que o navegador REALMENTE renderizou)
if ($res.solution.screenshot) {
    $pngPath = Join-Path $PSScriptRoot "pagina-vista.png"
    [IO.File]::WriteAllBytes($pngPath, [Convert]::FromBase64String($res.solution.screenshot))
    Write-Host "PRINT salvo em: $pngPath" -ForegroundColor Green
    Start-Process $pngPath
} else {
    Write-Host "(sem screenshot no retorno - provavelmente deu timeout antes de terminar)" -ForegroundColor Yellow
}

Start-Process $htmlPath
