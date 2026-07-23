# send-js.ps1
# Manda um directJs para o servidor local (que ja deve estar no ar via run-local.ps1
# e com a aba aquecida via send-request.ps1).
#
# O JS roda no console da aba ja aberta, um por vez (fila). O retorno vem SEMPRE em JSON
# dentro de solution.response.
#
# Contrato do JS:
#   - use `return` direto no topo, com `await` a vontade; OU declare uma funcao `main(args)`
#   - `args`  = o valor mandado em directJsArgs
#   - `sleep(ms)`
#   - `waitFor(fn, { timeout: 30000, interval: 100 })` -> espera em loop ate fn() ser truthy
#
# Uso:
#   .\send-js.ps1                              -> smoke test (return {ok:1, url:location.href})
#   .\send-js.ps1 -Suite                       -> roda a bateria de testes
#   .\send-js.ps1 -Queue                       -> 3 chamadas em paralelo p/ provar a fila
#   .\send-js.ps1 "return document.title"      -> roda o JS que voce passar

param(
    [string]$Js = "return {ok: 1, url: location.href, title: document.title}",
    [string]$Session = "session01",
    [int]$MaxTimeout = 180000,
    [switch]$Suite,
    [switch]$Queue
)

$Endpoint = "http://127.0.0.1:8191/v1"

function Invoke-DirectJs {
    param([string]$Code, $Args = $null, [string]$Label = "directJs")

    $payload = @{
        cmd        = "request.get"
        session    = $Session
        maxTimeout = $MaxTimeout
        directJs   = $Code
    }
    if ($null -ne $Args) { $payload.directJsArgs = $Args }
    $body = $payload | ConvertTo-Json -Depth 10

    Write-Host ""
    Write-Host "== $Label" -ForegroundColor Cyan
    Write-Host ($Code.Substring(0, [Math]::Min(120, $Code.Length))) -ForegroundColor DarkGray

    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
        $res = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType "application/json" -Body $body -TimeoutSec 300
        $sw.Stop()
        if ($res.status -eq "ok") {
            Write-Host "status  : ok  ($([Math]::Round($sw.Elapsed.TotalSeconds,1))s)" -ForegroundColor Green
            Write-Host "response: $($res.solution.response)"
        } else {
            Write-Host "status  : $($res.status)  ($([Math]::Round($sw.Elapsed.TotalSeconds,1))s)" -ForegroundColor Yellow
            Write-Host "message : $($res.message)" -ForegroundColor Yellow
        }
        return $res
    } catch {
        $sw.Stop()
        Write-Host "ERRO na chamada ($([Math]::Round($sw.Elapsed.TotalSeconds,1))s): $_" -ForegroundColor Red
        return $null
    }
}

if ($Suite) {
    Invoke-DirectJs -Code "return {ok: 1, url: location.href}" -Label "return simples"
    Invoke-DirectJs -Code "async function main(args) { await sleep(500); return args.n * 2 }" -Args @{ n = 21 } -Label "main() async + args + await  (espera 42)"
    Invoke-DirectJs -Code "return window.naoExiste.x" -Label "erro de runtime  (espera status error)"
    Invoke-DirectJs -Code "await waitFor(() => window.__nunca, {timeout: 3000}); return 1" -Label "waitFor timeout  (espera erro em ~3s, nao 30s)"
    Invoke-DirectJs -Code "return await waitFor(() => window._bigScriptString && 'presente', {timeout: 5000})" -Label "aba aquecida? (_bigScriptString presente)"
    return
}

if ($Queue) {
    Write-Host "Disparando 3 directJs em paralelo (cada um dorme 4s)..." -ForegroundColor Cyan
    Write-Host "Se a fila funciona, a ultima resposta traz os 3 pares na ordem start1,end1,start2,end2,..." -ForegroundColor DarkGray

    $code = "window.__t = window.__t || []; window.__t.push('start' + args.id); await sleep(4000); window.__t.push('end' + args.id); return window.__t"
    $jobs = 1..3 | ForEach-Object {
        $id = $_
        Start-Job -ScriptBlock {
            param($ep, $sess, $code, $id)
            $body = @{
                cmd = "request.get"; session = $sess; maxTimeout = 180000
                directJs = $code; directJsArgs = @{ id = $id }
            } | ConvertTo-Json -Depth 10
            $r = Invoke-RestMethod -Uri $ep -Method Post -ContentType "application/json" -Body $body -TimeoutSec 300
            "[$id] $($r.status) -> $($r.solution.response)"
        } -ArgumentList $Endpoint, $Session, $code, $id
    }
    $jobs | Wait-Job | Receive-Job | ForEach-Object { Write-Host $_ }
    $jobs | Remove-Job
    Write-Host ""
    Write-Host "Rode antes um  .\send-js.ps1 'delete window.__t; return 1'  para zerar o marcador." -ForegroundColor DarkGray
    return
}

Invoke-DirectJs -Code $Js
