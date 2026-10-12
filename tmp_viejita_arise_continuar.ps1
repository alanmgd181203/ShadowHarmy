# Viejita: pull regalo + preparar + despertar ejercito con --continuar (NO desde-cero).
$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Git = "C:\Program Files\Git\cmd\git.exe"
$Py = "C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
Set-Location $Root

Write-Output ("HOST=" + $env:COMPUTERNAME)
& $Git fetch origin
& $Git checkout regalo
& $Git pull origin regalo
Write-Output ("HEAD=" + (& $Git log -1 --oneline))

$env:PYTHONIOENCODING = "utf-8"
Write-Output "=== SMOKE CIRUGIA ==="
& $Py -u scripts\validar_beru_cirugia_engorde_iron_smoke.py
Write-Output ("SMOKE_EXIT=" + $LASTEXITCODE)

Write-Output "=== PREP CONTINUAR ==="
& $Py -u scripts\preparar_migracion_continuar_cirugia.py
Write-Output ("PREP_EXIT=" + $LASTEXITCODE)

Write-Output "=== DESPERTAR EJERCITO (continuar) ==="
& powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_despertar_ejercito.ps1"
$wakeExit = $LASTEXITCODE
Write-Output ("WAKE_EXIT=" + $wakeExit)

Start-Sleep -Seconds 10
Write-Output "=== PULSO ==="
if (Test-Path "$Root\scripts\_pulso_despertar.ps1") {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_pulso_despertar.ps1"
}

$bat = Get-ChildItem "$Root\data\beru\rango\vigilante_flota\run_CAMP_*.bat" -ErrorAction SilentlyContinue | Select-Object -First 2
foreach ($b in $bat) {
  Write-Output ("BAT=" + $b.Name)
  Select-String -Path $b.FullName -Pattern "desde-cero|continuar" | ForEach-Object { Write-Output ("  " + $_.Line.Trim()) }
}

exit $wakeExit
