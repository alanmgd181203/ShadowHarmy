# Shadow Army - Despertar Santos Beru rango FERIA (Windows, background)
# Perfil feria: orejas 2,2% (Vacío/Sangre) · Oz 0,2% · Red 1,2% simétrica L=S.
# Sellos aislados: manos_feria_* (no pisa manos_informe.json normal).
#
# Uso:
#   .\scripts\despertar_santos_feria_win.ps1 -Santos VVV,HYPE,LIT
#   .\scripts\despertar_santos_feria_win.ps1 -Santos VVV -Continuar
param(
    [Parameter(Mandatory = $true)]
    [string]$Santos,
    [int]$OjosSegundos = 45,
    [int]$EscalonSegundos = 45,
    [switch]$Continuar,
    [switch]$SinOjos
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
    $existing = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "python" -and $_.CommandLine -match "arise_beru_rango_manos" } |
        Select-Object -First 1
    if ($existing -and $existing.ExecutablePath -and (Test-Path $existing.ExecutablePath)) {
        return $existing.ExecutablePath
    }
    return (Get-Command python -ErrorAction Stop).Source
}

$PythonExe = Resolve-PythonExe

$list = @(
    $Santos -split "[,;]" |
        ForEach-Object { $_.Trim().ToUpper() } |
        Where-Object { $_ }
)
if ($list.Count -eq 0) {
    Write-Error "Lista vacia"
}

$env:BERU_RANGO_PERFIL = "feria"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"
$env:BERU_RANGO_MANOS = "false"

Write-Host ""
Write-Host "=== DESPERTAR FERIA - $($list -join ', ') ===" -ForegroundColor Magenta
Write-Host "Perfil feria (x2) · IGRIS max lev · escalon ${EscalonSegundos}s" -ForegroundColor Gray

foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$ojosProcId = $null
if (-not $SinOjos -and $OjosSegundos -gt 0) {
    $csv = $list -join ","
    Write-Host ""
    Write-Host "Ojos flota $OjosSegundos s: $csv" -ForegroundColor Yellow
    $ojosLog = Join-Path $Root "data\beru\rango\ojos_feria_despertar_stdout.log"
    $ojosErr = Join-Path $Root "data\beru\rango\ojos_feria_despertar_stderr.log"
    $ojosProc = Start-Process -FilePath $PythonExe `
        -ArgumentList @("-u", "scripts/arise_beru_rango_ojos.py", "--santos", $csv) `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $ojosLog `
        -RedirectStandardError $ojosErr `
        -PassThru -WindowStyle Hidden
    $ojosProcId = $ojosProc.Id
    Start-Sleep -Seconds $OjosSegundos
    try { Stop-Process -Id $ojosProcId -Force -ErrorAction SilentlyContinue } catch {}
    Write-Host "Ojos cerrados (proc $ojosProcId)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Manos GO (feria):" -ForegroundColor Yellow
$env:BERU_RANGO_MANOS = "true"
$launched = @()

foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    $pyArgs = @(
        "-u", "scripts/arise_beru_rango_manos.py",
        "--activo", $s,
        "--perfil", "feria",
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
        -RedirectStandardOutput (Join-Path $dir "manos_feria_stdout.log") `
        -RedirectStandardError (Join-Path $dir "manos_feria_stderr.log") `
        -PassThru -WindowStyle Hidden
    $launched += [PSCustomObject]@{ Santo = $s; ProcId = $proc.Id }
    Write-Host "  $s -> proc $($proc.Id)" -ForegroundColor Green
    if ($s -ne $list[-1]) {
        Start-Sleep -Seconds $EscalonSegundos
    }
}

Write-Host ""
Write-Host "Despertar feria lanzado. Revisar manos_feria_stderr.log por Santo." -ForegroundColor Cyan
$launched | Format-Table -AutoSize
