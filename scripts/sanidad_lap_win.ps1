# Shadow Army - Sanidad de la lap (Windows)
# Libera RAM de panel/tunel/ojos duplicados; dedupe manos; NO mata manos sanas (1 por Santo).
#
# Uso:
#   .\scripts\sanidad_lap_win.ps1
#   .\scripts\sanidad_lap_win.ps1 -DryRun
#   .\scripts\sanidad_lap_win.ps1 -SinPanel
param(
    [switch]$DryRun,
    [switch]$SinPanel
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Get-RamMb {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    if (-not $os) { return $null }
    [PSCustomObject]@{
        LibreMb = [math]::Round($os.FreePhysicalMemory / 1024, 0)
        TotalMb = [math]::Round($os.TotalVisibleMemorySize / 1024, 0)
    }
}

function Get-BeruProcs {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "python" -and $_.CommandLine -match "arise_beru_rango" }
}

function Get-ActivoFromCmd {
    param([string]$Cmd)
    if ($Cmd -match "--activo\s+([A-Za-z0-9]+)") { return $matches[1].ToUpper() }
    return $null
}

function Get-ProcScore {
    param([string]$Cmd)
    if ($Cmd -match "pythoncore") { return 2 }
    if ($Cmd -match "WindowsApps") { return 0 }
    return 1
}

function Stop-PidSafe {
    param([int]$ProcId, [string]$Motivo)
    if ($ProcId -le 0) { return }
    if ($DryRun) {
        Write-Host "  [dry-run] matar proc $ProcId ($Motivo)" -ForegroundColor DarkGray
        return
    }
    try {
        Stop-Process -Id $ProcId -Force -ErrorAction Stop
        Write-Host "  matado proc $ProcId ($Motivo)" -ForegroundColor DarkYellow
    } catch {
        Write-Host "  no pude matar proc $ProcId : $_" -ForegroundColor Red
    }
}

$ramAntes = Get-RamMb
Write-Host ""
Write-Host "=== SANIDAD LAP - Beru rango ===" -ForegroundColor Cyan
if ($ramAntes) {
    Write-Host ("RAM libre: {0} MB / {1} MB" -f $ramAntes.LibreMb, $ramAntes.TotalMb) -ForegroundColor Gray
}

if (-not $SinPanel) {
    Write-Host ""
    Write-Host "[1] Deteniendo panel (Vite + tunel)..." -ForegroundColor Yellow
    if ($DryRun) {
        Write-Host "  [dry-run] detener_panel_win.ps1" -ForegroundColor DarkGray
    } else {
        & (Join-Path $Root "scripts\detener_panel_win.ps1")
    }
} else {
    Write-Host ""
    Write-Host "[1] Panel intacto (-SinPanel)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[2] Ojos Beru (duplicados / flota)..." -ForegroundColor Yellow
$ojos = @(Get-BeruProcs | Where-Object { $_.CommandLine -match "arise_beru_rango_ojos" })
if ($ojos.Count -eq 0) {
    Write-Host "  ningun proceso ojos" -ForegroundColor Green
} else {
    foreach ($p in $ojos) {
        Stop-PidSafe -ProcId $p.ProcessId -Motivo "ojos flota"
    }
}

Write-Host ""
Write-Host "[3] Manos - dedupe por Santo..." -ForegroundColor Yellow
$manos = @()
foreach ($p in (Get-BeruProcs | Where-Object { $_.CommandLine -match "arise_beru_rango_manos" })) {
    $act = Get-ActivoFromCmd $p.CommandLine
    if ($act) {
        $manos += [PSCustomObject]@{
            ProcId = $p.ProcessId
            Activo = $act
            Score  = (Get-ProcScore $p.CommandLine)
        }
    }
}
$grupos = $manos | Group-Object Activo
$dupes = 0
foreach ($g in $grupos) {
    if ($g.Count -le 1) { continue }
    $dupes += ($g.Count - 1)
    $keep = ($g.Group | Sort-Object Score, ProcId -Descending | Select-Object -First 1).ProcId
    foreach ($row in ($g.Group | Where-Object { $_.ProcId -ne $keep })) {
        Stop-PidSafe -ProcId $row.ProcId -Motivo "manos duplicado $($g.Name) (conservo $keep)"
    }
}
if ($dupes -eq 0) {
    Write-Host ("  {0} manos, 0 duplicados" -f $grupos.Count) -ForegroundColor Green
} else {
    Write-Host ("  eliminados {0} duplicados, quedan {1} Santos" -f $dupes, $grupos.Count) -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4] Ritual colgado (smoke/preparar/juicio)..." -ForegroundColor Yellow
$zombiePat = "validar_beru|preparar_beru|teatro_beru|beru_spot_kline"
$zombies = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "python" -and $_.CommandLine -match $zombiePat }
if (-not $zombies) {
    Write-Host "  ninguno" -ForegroundColor Green
} else {
    foreach ($p in $zombies) {
        Stop-PidSafe -ProcId $p.ProcessId -Motivo "ritual colgado"
    }
}

Write-Host ""
Write-Host "[5] Inventario Beru vivo:" -ForegroundColor Cyan
$vivo = @()
foreach ($p in (Get-BeruProcs | Where-Object { $_.CommandLine -match "arise_beru_rango_manos" })) {
    $act = Get-ActivoFromCmd $p.CommandLine
    if ($act) { $vivo += [PSCustomObject]@{ Santo = $act; ProcId = $p.ProcessId } }
}
$vivo | Sort-Object Santo | Format-Table -AutoSize

$ramDespues = Get-RamMb
if ($ramAntes -and $ramDespues) {
    $delta = $ramDespues.LibreMb - $ramAntes.LibreMb
    $sign = if ($delta -ge 0) { "+" } else { "" }
    Write-Host ("RAM libre ahora: {0} MB ({1}{2} MB)" -f $ramDespues.LibreMb, $sign, $delta) -ForegroundColor Gray
}

$report = @{
    ts             = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    ts_utc         = (Get-Date).ToUniversalTime().ToString('o')
    dry_run        = [bool]$DryRun
    sin_panel      = [bool]$SinPanel
    ram_antes_mb   = if ($ramAntes) { $ramAntes.LibreMb } else { $null }
    ram_despues_mb = if ($ramDespues) { $ramDespues.LibreMb } else { $null }
    n_manos        = @($vivo).Count
    santos         = @($vivo | ForEach-Object { $_.Santo })
    ojos_muertos   = @($ojos | ForEach-Object { $_.ProcessId })
}
$outPath = Join-Path $Root "data\beru\rango\sanidad_lap.json"
if (-not $DryRun) {
    $report | ConvertTo-Json -Depth 4 | Set-Content -Path $outPath -Encoding UTF8
    Write-Host "Sello: $outPath" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Sanidad lista. Manos sanas intactas." -ForegroundColor Green
