# Migra un lote: apaga manos NORMAL lineal -> despierta FERIA
param(
    [Parameter(Mandatory = $true)]
    [string]$Santos,
    [int]$EscalonSegundos = 45,
    [switch]$SinOjos
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$list = @($Santos -split "[,;]" | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ })
if ($list.Count -eq 0) { Write-Error "Lista vacia" }

Write-Host ""
Write-Host "=== MIGRAR LOTE -> FERIA ($($list.Count) Santos) ===" -ForegroundColor Magenta

$killed = @()
foreach ($s in $list) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match "python" -and
            $_.CommandLine -match "arise_beru_rango_manos" -and
            $_.CommandLine -match "--activo $s\b" -and
            $_.CommandLine -notmatch "--mercado inverse" -and
            $_.CommandLine -notmatch "--perfil feria"
        } |
        ForEach-Object {
            Write-Host "  Matar normal $s PID $($_.ProcessId)" -ForegroundColor DarkYellow
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += [PSCustomObject]@{ Santo = $s; PID = $_.ProcessId; Tipo = "normal" }
        }
    # feria duplicado previo (relanzar limpio)
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match "python" -and
            $_.CommandLine -match "arise_beru_rango_manos" -and
            $_.CommandLine -match "--activo $s\b" -and
            $_.CommandLine -notmatch "--mercado inverse" -and
            $_.CommandLine -match "--perfil feria"
        } |
        ForEach-Object {
            Write-Host "  Matar feria dup $s PID $($_.ProcessId)" -ForegroundColor DarkRed
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += [PSCustomObject]@{ Santo = $s; PID = $_.ProcessId; Tipo = "feria_dup" }
        }
}

Start-Sleep -Seconds 2
Write-Host "  Procesos matados: $($killed.Count)" -ForegroundColor Gray

$feriaArgs = @{
    Santos          = ($list -join ",")
    EscalonSegundos = $EscalonSegundos
}
if ($SinOjos) { $feriaArgs.SinOjos = $true }
& (Join-Path $Root "scripts\despertar_santos_feria_win.ps1") @feriaArgs

Write-Host ""
Write-Host "=== AUDITORIA LOTE ===" -ForegroundColor Cyan
$ok = 0; $fail = 0
foreach ($s in $list) {
    $inf = Join-Path $Root "data\beru\rango\$s\manos_feria_informe.json"
    $errLog = Join-Path $Root "data\beru\rango\$s\manos_feria_stderr.log"
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match "python" -and
            $_.CommandLine -match "arise_beru_rango_manos" -and
            $_.CommandLine -match "--activo $s\b" -and
            $_.CommandLine -match "--perfil feria"
        })
    $est = "NO_INF"; $errs = 0; $manos = $false
    if (Test-Path $inf) {
        try {
            $j = Get-Content $inf -Raw | ConvertFrom-Json
            $est = $j.snapshot.vivo.estado
            $errs = $j.contadores.errores
            $manos = $j.manos
        } catch { $est = "PARSE_ERR" }
    }
    $nProc = $procs.Count
    $flag = if ($est -eq "ACECHANDO" -and $errs -eq 0 -and $nProc -eq 1) { "OK"; $ok++ } else { "!!"; $fail++ }
    $color = if ($flag -eq "OK") { "Green" } else { "Red" }
    Write-Host ("  [{0}] {1,-10} proc={2} estado={3,-12} err={4}" -f $flag, $s, $nProc, $est, $errs) -ForegroundColor $color
    if ($nProc -gt 1) {
        $procs | ForEach-Object { Write-Host "       DUP PID $($_.ProcessId)" -ForegroundColor Red }
    }
    if (Test-Path $errLog) {
        $tail = Get-Content $errLog -Tail 1 -ErrorAction SilentlyContinue
        if ($tail -match "Error|Traceback") { Write-Host "       stderr: $tail" -ForegroundColor Red }
    }
}
Write-Host ""
Write-Host "Lote: OK=$ok FAIL=$fail" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
