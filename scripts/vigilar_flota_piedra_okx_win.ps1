# Shadow Army - Vigilante flota piedra OKX (auto-relance tras luz/red)
#
# Mantiene 115/115 manos: dedupe + relanza caidos con --continuar.
#
# Uso:
#   .\scripts\vigilar_flota_piedra_okx_win.ps1
#   .\scripts\vigilar_flota_piedra_okx_win.ps1 -UnaVez
#   .\scripts\vigilar_flota_piedra_okx_win.ps1 -InstalarTarea
#   .\scripts\vigilar_flota_piedra_okx_win.ps1 -Intervalo 300
param(
    [int]$Intervalo = 300,
    [int]$Escalon = 30,
    [switch]$UnaVez,
    [switch]$DryRun,
    [switch]$InstalarTarea,
    [switch]$QuitarTarea
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
$TaskName = "ShadowHarmy_VigilanteFlotaPiedra"
$LogOut = Join-Path $Root "data\beru\rango\vigilante_flota_loop.log"
$LogErr = Join-Path $Root "data\beru\rango\vigilante_flota_loop_stderr.log"

if ($QuitarTarea) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Tarea $TaskName eliminada." -ForegroundColor Yellow
    exit 0
}

if ($InstalarTarea) {
    $psArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $Root "scripts\vigilar_flota_piedra_okx_win.ps1"),
        "-Intervalo", $Intervalo
    )
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($psArgs -join " ") -WorkingDirectory $Root
    $trigger1 = New-ScheduledTaskTrigger -AtLogOn
    $trigger2 = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Force | Out-Null
    Write-Host "Tarea instalada: $TaskName (logon + arranque)" -ForegroundColor Green
    Write-Host "Logs: $LogOut" -ForegroundColor Gray
    exit 0
}

$pyArgs = @(
    "-u", "scripts/vigilar_flota_piedra_okx.py",
    "--intervalo", $Intervalo,
    "--escalon", $Escalon
)
if ($UnaVez) { $pyArgs += "--una-vez" }
if ($DryRun) { $pyArgs += "--dry-run" }

Write-Host ""
Write-Host "=== VIGILANTE FLOTA PIEDRA OKX ===" -ForegroundColor Cyan
Write-Host "Python: $PythonExe" -ForegroundColor Gray
Write-Host "Intervalo: ${Intervalo}s · Escalon relanzar: ${Escalon}s" -ForegroundColor Gray

$env:BERU_MAR = "okx"
$env:BERU_RANGO_PERFIL = "piedra"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"

if ($UnaVez -or $DryRun) {
    & $PythonExe @pyArgs
    exit $LASTEXITCODE
}

# Loop persistente en ventana oculta (un solo proceso)
$proc = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "vigilar_flota_piedra_okx.py" -and $_.CommandLine -notmatch "una-vez" }
if ($proc) {
    Write-Host "Vigilante ya corre (pid $($proc.ProcessId))." -ForegroundColor Yellow
    exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path $LogOut) | Out-Null
Start-Process -FilePath $PythonExe `
    -ArgumentList $pyArgs `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $LogOut `
    -RedirectStandardError $LogErr `
    -WindowStyle Hidden `
    -PassThru | ForEach-Object {
        Write-Host "Vigilante flota iniciado pid=$($_.Id)" -ForegroundColor Green
        Write-Host "Log: $LogOut" -ForegroundColor Gray
    }
