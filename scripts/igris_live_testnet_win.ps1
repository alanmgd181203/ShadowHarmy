# Igris LIVE TESTNET — PowerShell (Windows) checklist 3.10.7b
#   .\scripts\igris_live_testnet_win.ps1
#   .\scripts\igris_live_testnet_win.ps1 -Segundos 90 -Activos "ETH,BTC,LTC"
param(
    [double]$Segundos = 90,
    [string]$Activos = "ETH,BTC,LTC,SOL,OP"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:LIVE_IGRIS_TESTNET = "true"
$env:LIVE_IGRIS_SEGUNDOS_OJOS = "$Segundos"
$env:LIVE_IGRIS_ACTIVOS = $Activos
$env:LIVE_IGRIS_MORDIDA_MAX_USD = if ($env:LIVE_IGRIS_MORDIDA_MAX_USD) { $env:LIVE_IGRIS_MORDIDA_MAX_USD } else { "12" }
$env:MODO_TESTNET = "True"
$env:MODO_SIMULACION = "False"
$env:ARENA_IGRIS_ACTIVA = "false"
$env:ARENA_IGRIS_FILLS_VIRTUALES = "false"
$env:GREED_KAISER_ENABLED = "false"
$env:GREED_VIP_ENABLED = "false"
$env:GREED_BASIS_HOLD_ENABLED = "false"
$env:SAFE_MODE = "true"

$minutos = [math]::Round($Segundos / 60.0, 1)
Write-Host ""
Write-Host "=== Shadow Army — Igris LIVE TESTNET (3.10.7b) ===" -ForegroundColor Cyan
Write-Host ("Manos DEMO · Ojos: {0}s (~{1} min) · Activos: {2}" -f $Segundos, $minutos, $Activos)
Write-Host ""

if (Test-Path "$Root\.venv\Scripts\Activate.ps1") {
    & "$Root\.venv\Scripts\Activate.ps1"
}

python scripts/validar_igris_smoke.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/igris_live_testnet.py --segundos $Segundos --activos $Activos
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$reporte = Join-Path $Root "data\igris_live_testnet_report.json"
Write-Host ""
Write-Host "Reporte: $reporte" -ForegroundColor Green
Write-Host "Lee el campo veredicto (PASS_LIVE = cerrar 3.10.7b)."
