# Shadow Army — Despertar Santos Beru piedra OKX (semáforo verde)
# Mar OKX · perfil piedra · manos live con --manos-go
#
# Uso:
#   .\scripts\despertar_piedra_verde_okx_win.ps1
#   .\scripts\despertar_piedra_verde_okx_win.ps1 -Santos AEON,GRAM
#   .\scripts\despertar_piedra_verde_okx_win.ps1 -Continuar
param(
    [string]$Santos = "",
    [int]$OjosSegundos = 60,
    [int]$EscalonSegundos = 45,
    [switch]$Continuar,
    [switch]$SinOjos,
    [switch]$SoloPreparar
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Resolve-PythonExe {
    $candidates = @(
        "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return (Get-Command python -ErrorAction Stop).Source
}

$PythonExe = Resolve-PythonExe
$ListaPath = Join-Path $Root "data\beru\rango\piedra_verde_santos.txt"

if ($Santos -and $Santos.Trim()) {
    $list = @(
        $Santos -split "[,;]" |
            ForEach-Object { $_.Trim().ToUpper() } |
            Where-Object { $_ -and $_ -notmatch "^#" }
    )
} elseif (Test-Path $ListaPath) {
    $list = @(
        Get-Content $ListaPath |
            ForEach-Object { $_.Trim().ToUpper() } |
            Where-Object { $_ -and $_ -notmatch "^#" }
    )
} else {
    Write-Error "Sin lista verde — pasa -Santos o crea piedra_verde_santos.txt"
}

if ($list.Count -eq 0) {
    Write-Error "Lista vacia"
}

$env:BERU_MAR = "okx"
$env:BERU_RANGO_PERFIL = "piedra"
$env:BERU_RANGO_MERCADO = "linear"
$env:BERU_RANGO_MANOS = "false"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"

Write-Host ""
Write-Host "=== PIEDRA OKX — VERDE ($($list -join ', ')) ===" -ForegroundColor Cyan
Write-Host "Mar OKX · perfil piedra · escalon ${EscalonSegundos}s" -ForegroundColor Gray

Write-Host ""
Write-Host "Ritual preparacion..." -ForegroundColor Yellow
& $PythonExe scripts/revisar_pre_despertar_piedra_okx.py
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Pre-despertar con avisos/bloqueos — revisar pre_despertar_piedra_okx.json"
}

$env:BERU_RANGO_PERFIL = "piedra"
& $PythonExe scripts/preparar_beru_rango_ejercito.py
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Preparar ejercito con fallos — revisar preparar_sanidad.json"
}

& $PythonExe scripts/validar_beru_okx_smoke.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Smoke OKX fallo — corregir antes de manos"
}

& $PythonExe scripts/validar_beru_rango_piedra_smoke.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Smoke piedra fallo — corregir antes de manos"
}

if ($SoloPreparar) {
    Write-Host ""
    Write-Host "Solo preparar: listo. Sin ojos ni manos." -ForegroundColor Green
    exit 0
}

foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$ojosProcId = $null
if (-not $SinOjos -and $OjosSegundos -gt 0) {
    $csv = $list -join ","
    Write-Host ""
    Write-Host "Ojos flota $OjosSegundos s: $csv" -ForegroundColor Yellow
    $ojosLog = Join-Path $Root "data\beru\rango\ojos_piedra_verde_stdout.log"
    $ojosErr = Join-Path $Root "data\beru\rango\ojos_piedra_verde_stderr.log"
    $env:BERU_MAR = "okx"
    $env:BERU_RANGO_PERFIL = "piedra"
    $env:BERU_RANGO_MANOS = "false"
    $env:MODO_SIMULACION = "true"
    $ojosProc = Start-Process -FilePath $PythonExe `
        -ArgumentList @("-u", "scripts/arise_beru_rango_ojos.py", "--santos", $csv) `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $ojosLog `
        -RedirectStandardError $ojosErr `
        -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds $OjosSegundos
    try { Stop-Process -Id $ojosProc.Id -Force -ErrorAction SilentlyContinue } catch {}
    $ojosProcId = $ojosProc.Id
    Write-Host "Ojos cerrados (proc $ojosProcId)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Manos GO (OKX live):" -ForegroundColor Yellow
$env:BERU_RANGO_MANOS = "true"
$env:MODO_SIMULACION = "false"
$launched = @()

foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    $pyArgs = @(
        "-u", "scripts/arise_beru_rango_manos.py",
        "--activo", $s,
        "--perfil", "piedra",
        "--manos-go"
    )
    if ($Continuar) {
        $pyArgs += "--continuar"
    } else {
        $pyArgs += "--desde-cero"
    }
    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList $pyArgs `
        -WorkingDirectory $Root `
        -RedirectStandardOutput (Join-Path $dir "manos_piedra_stdout.log") `
        -RedirectStandardError (Join-Path $dir "manos_piedra_stderr.log") `
        -PassThru -WindowStyle Hidden
    $launched += [PSCustomObject]@{ Santo = $s; ProcId = $proc.Id }
    Write-Host "  $s -> proc $($proc.Id)" -ForegroundColor Green
    if ($s -ne $list[-1]) {
        Start-Sleep -Seconds $EscalonSegundos
    }
}

Write-Host ""
Write-Host "Piedra verde despertada. Revisar manos_piedra_stderr.log por Santo." -ForegroundColor Cyan
$launched | Format-Table -AutoSize
