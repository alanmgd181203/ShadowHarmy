# Arena Igris ~2 min — PowerShell (Windows)
# Uso:
#   .\scripts\arena_igris_win.ps1
#   .\scripts\arena_igris_win.ps1 -Segundos 120 -Activos "ETH,BTC"
param(
    [double]$Segundos = 120,
    [string]$Activos = "flota"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:ARENA_IGRIS_ACTIVA = "true"
$env:ARENA_IGRIS_FILLS_VIRTUALES = "true"
$env:ARENA_IGRIS_SIN_RANGOS = "true"
$env:ARENA_IGRIS_SIN_PACIENCIA = "true"
$env:ARENA_IGRIS_SIN_BANDA_DELTA = "true"
$env:ARENA_IGRIS_TUSK_LIMPIO_POR_ACTIVO = "true"
$env:ARENA_IGRIS_SEGUNDOS_OJOS = "$Segundos"
$env:ARENA_IGRIS_ACTIVOS = $Activos
$env:MODO_SIMULACION = "true"

Write-Host ""
Write-Host "=== Shadow Army — Arena Igris (Windows) ===" -ForegroundColor Cyan
Write-Host "Ojos: ${Segundos}s (~$([math]::Round($Segundos/60,1)) min) · Activos: $Activos"
Write-Host ""

if (Test-Path "$Root\.venv\Scripts\Activate.ps1") {
    & "$Root\.venv\Scripts\Activate.ps1"
}

python scripts/validar_igris_smoke.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/arena_igris_aislado.py --segundos $Segundos
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Reporte: $Root\data\arena_igris_report.json" -ForegroundColor Green
Write-Host "Historial: $Root\data\historial_hierro.jsonl"
