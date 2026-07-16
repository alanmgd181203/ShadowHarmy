# Beru Live Testnet — Windows (opcional; Jess México usa Mac)
# Uso: .\scripts\beru_live_testnet_win.ps1 [-Segundos 1800] [-Activos "ETH,BTC,LTC,SOL,OP"]
param(
    [double]$Segundos = 1800,
    [string]$Activos = "ETH,BTC,LTC,SOL,OP",
    [double]$Mordida = 10
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:LIVE_BERU_TESTNET = "true"
$env:LIVE_BERU_SEGUNDOS = "$Segundos"
$env:LIVE_BERU_ACTIVOS = $Activos
$env:BERU_CAZADOR_MORDIDA_USD = "$Mordida"
$env:BERU_CAZA_CAPA1_USD = "$Mordida"
$env:BERU_TIER_DEFAULT = "PLENO"
$env:BERU_MODO_COMBATE_DEFAULT = "CAZA"
$env:BERU_VACIO_ANSIEDAD = "0.012"
$env:MODO_TESTNET = "True"
$env:MODO_SIMULACION = "False"
$env:GREED_KAISER_ENABLED = "false"
$env:GREED_VIP_ENABLED = "false"
$env:GREED_BASIS_HOLD_ENABLED = "false"
$env:SAFE_MODE = "true"

if (Test-Path "$Root\.venv\Scripts\Activate.ps1") {
    & "$Root\.venv\Scripts\Activate.ps1"
}

Write-Host "[live-win] Beru ${Segundos}s · $Activos · Ansiedad/Mariscal/`$$Mordida"
python scripts/validar_beru_cazador_smoke.py
python scripts/beru_live_testnet.py --segundos $Segundos --activos $Activos
Write-Host "[live-win] reporte → data/beru_live_testnet_report.json"
