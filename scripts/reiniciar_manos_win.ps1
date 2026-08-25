# Shadow Army - Reiniciar manos Beru rango (Windows) con --continuar
# Mata manos actuales y las relanza con el codigo nuevo. NO --desde-cero.
#
# Uso:
#   .\scripts\reiniciar_manos_win.ps1
#   .\scripts\reiniciar_manos_win.ps1 -EscalonSegundos 12
param(
    [int]$EscalonSegundos = 12,
    [switch]$DryRun
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

function Get-ManosRows {
    $rows = @()
    foreach ($p in (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "python" -and $_.CommandLine -match "arise_beru_rango_manos" })) {
        if ($p.CommandLine -match "--activo\s+([A-Za-z0-9]+)") {
            $rows += [PSCustomObject]@{
                Santo  = $matches[1].ToUpper()
                ProcId = $p.ProcessId
            }
        }
    }
    return $rows
}

$PythonExe = Resolve-PythonExe
Write-Host "Python: $PythonExe" -ForegroundColor Gray

$antes = @(Get-ManosRows | Sort-Object Santo)
if ($antes.Count -eq 0) {
    Write-Error "No hay manos vivas para reiniciar"
}
$list = @($antes | Select-Object -ExpandProperty Santo -Unique)
Write-Host ""
Write-Host "=== REINICIO MANOS --continuar ($($list.Count) Santos) ===" -ForegroundColor Cyan
Write-Host ($list -join ", ") -ForegroundColor Gray

# 1) Matar manos actuales
Write-Host ""
Write-Host "[1] Deteniendo manos..." -ForegroundColor Yellow
foreach ($row in $antes) {
    if ($DryRun) {
        Write-Host "  [dry-run] matar $($row.Santo) proc $($row.ProcId)" -ForegroundColor DarkGray
        continue
    }
    try {
        Stop-Process -Id $row.ProcId -Force -ErrorAction Stop
        Write-Host "  parado $($row.Santo) ($($row.ProcId))" -ForegroundColor DarkYellow
    } catch {
        Write-Host "  skip $($row.Santo): $_" -ForegroundColor Red
    }
}
Start-Sleep -Seconds 2

$restos = @(Get-ManosRows)
if ($restos.Count -gt 0 -and -not $DryRun) {
    foreach ($r in $restos) {
        try { Stop-Process -Id $r.ProcId -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Seconds 1
}

# 2) Relanzar --continuar
Write-Host ""
Write-Host "[2] Relanzando --manos-go --continuar (escalon ${EscalonSegundos}s)..." -ForegroundColor Yellow
$env:BERU_RANGO_PERFIL = "normal"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"
$env:BERU_RANGO_MANOS = "true"

$launched = @()
foreach ($s in $list) {
    $dir = Join-Path $Root "data\beru\rango\$s"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $outLog = Join-Path $dir "manos_stdout.log"
    $errLog = Join-Path $dir "manos_stderr.log"
    # Append marker then overwrite redirect for new session
    Add-Content -Path $outLog -Value "`n=== REINICIO CONTINUAR $(Get-Date -Format o) ===`n" -ErrorAction SilentlyContinue

    if ($DryRun) {
        Write-Host "  [dry-run] $s --continuar" -ForegroundColor DarkGray
        continue
    }
    $pyArgs = @(
        "-u", "scripts/arise_beru_rango_manos.py",
        "--activo", $s, "--manos-go", "--continuar"
    )
    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList $pyArgs `
        -WorkingDirectory $Root `
        -RedirectStandardOutput (Join-Path $dir "manos_restart_stdout.log") `
        -RedirectStandardError (Join-Path $dir "manos_restart_stderr.log") `
        -PassThru -WindowStyle Hidden
    $launched += [PSCustomObject]@{ Santo = $s; ProcId = $proc.Id }
    Write-Host "  $s -> proc $($proc.Id)" -ForegroundColor Green
    if ($s -ne $list[-1]) {
        Start-Sleep -Seconds $EscalonSegundos
    }
}

Write-Host ""
Write-Host "Reinicio lanzado. Verificar inventario." -ForegroundColor Cyan
$launched | Format-Table -AutoSize
