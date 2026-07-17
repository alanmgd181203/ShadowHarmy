# Beru Live Testnet — Windows (opcional; Jess México usa Mac)
# Uso: .\scripts\beru_live_testnet_win.ps1 [-Segundos 3600] [-Activos "flota"]
param(
    [double]$Segundos = 3600,
    [string]$Activos = "flota",
    [double]$Mordida = 20,
    [int]$Leverage = 10
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:LIVE_BERU_TESTNET = "true"
$env:LIVE_BERU_SEGUNDOS = "$Segundos"
$env:LIVE_BERU_ACTIVOS = $Activos
$env:LIVE_BERU_MORDIDA_USD = "$Mordida"
$env:BERU_CAZADOR_MORDIDA_USD = "$Mordida"
$env:BERU_CAZA_CAPA1_USD = "$Mordida"
$env:BERU_TIER_DEFAULT = "PLENO"
$env:BERU_MODO_COMBATE_DEFAULT = "CAZA"
$env:BERU_VACIO_ANSIEDAD = "0.012"
$env:BERU_SPOT_MARGEN_ENABLED = "true"
$env:BERU_SPOT_MARGEN_LEVERAGE = "$Leverage"
$env:BERU_RAIL_USDT_ONLY = "true"
$env:MODO_TESTNET = "True"
$env:MODO_SIMULACION = "False"
$env:GREED_KAISER_ENABLED = "false"
$env:GREED_VIP_ENABLED = "false"
$env:GREED_BASIS_HOLD_ENABLED = "false"
$env:SAFE_MODE = "true"

if (Test-Path "$Root\.venv\Scripts\Activate.ps1") {
    & "$Root\.venv\Scripts\Activate.ps1"
}

Write-Host "[live-win] Beru ${Segundos}s · $Activos · Ansiedad/Mariscal/`$$Mordida · margen ${Leverage}x USDT"
python scripts/validar_beru_cazador_smoke.py
python scripts/beru_live_testnet.py --segundos $Segundos --activos $Activos
Write-Host "[live-win] reporte → data/beru_live_testnet_report.json"
