# Shadow Army - Despertar Santos Beru rango (Windows, background)
# Ojos breve -> manos escalonadas (--desde-cero si primera vez).
#
# Uso:
#   .\scripts\despertar_santos_win.ps1 -Santos TRB,ESP,MUBARAK,UB
#   .\scripts\despertar_santos_win.ps1 -Santos TRB -Continuar
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

$env:BERU_RANGO_PERFIL = "normal"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"
$env:BERU_RANGO_MANOS = "false"

Write-Host ""
Write-Host "=== DESPERTAR - $($list -join ', ') ===" -ForegroundColor Cyan
Write-Host "Perfil normal, IGRIS max lev, escalon ${EscalonSegundos}s" -ForegroundColor Gray

foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$ojosProcId = $null
if (-not $SinOjos -and $OjosSegundos -gt 0) {
    $csv = $list -join ","
    Write-Host ""
    Write-Host "Ojos flota $OjosSegundos s: $csv" -ForegroundColor Yellow
    $ojosLog = Join-Path $Root "data\beru\rango\ojos_despertar_stdout.log"
    $ojosErr = Join-Path $Root "data\beru\rango\ojos_despertar_stderr.log"
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
Write-Host "Manos GO:" -ForegroundColor Yellow
$env:BERU_RANGO_MANOS = "true"
$launched = @()

foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    $pyArgs = @("-u", "scripts/arise_beru_rango_manos.py", "--activo", $s, "--manos-go")
    if ($Continuar) {
        $pyArgs += "--continuar"
    } else {
        $pyArgs += "--desde-cero"
    }
    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList $pyArgs `
        -WorkingDirectory $Root `
        -RedirectStandardOutput (Join-Path $dir "manos_stdout.log") `
        -RedirectStandardError (Join-Path $dir "manos_stderr.log") `
        -PassThru -WindowStyle Hidden
    $launched += [PSCustomObject]@{ Santo = $s; ProcId = $proc.Id }
    Write-Host "  $s -> proc $($proc.Id)" -ForegroundColor Green
    if ($s -ne $list[-1]) {
        Start-Sleep -Seconds $EscalonSegundos
    }
}

Write-Host ""
Write-Host "Despertar lanzado. Revisar manos_stderr.log por Santo si algo falla." -ForegroundColor Cyan
$launched | Format-Table -AutoSize
