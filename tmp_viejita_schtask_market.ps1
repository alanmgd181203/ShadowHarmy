# Despertar Igris market via schtasks (sobrevive al SSH)
$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Bat = "$Root\tmp_arise_igris_viejita.bat"
$Task = "ShadowHarmy_AriseIgrisEscudo"
$BatCopy = "C:\Users\lenovo\tmp_arise_igris_viejita.bat"

Copy-Item -Force $Bat $BatCopy
Write-Host "BAT=$BatCopy"

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -and $_.CommandLine -match "arise_igris_escudo_btc" } |
  ForEach-Object {
    Write-Host "STOP $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
Start-Sleep -Seconds 2

$log = Join-Path $Root "data\logs\arise_igris_escudo_out.log"
$err = Join-Path $Root "data\logs\arise_igris_escudo_err.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Add-Content -Path $log -Value "`r`n=== schtask market $(Get-Date -Format o) ===`r`n" -Encoding utf8

cmd /c "schtasks /Delete /TN $Task /F >nul 2>&1"
$st = (Get-Date).AddMinutes(3).ToString("HH:mm")
cmd /c "schtasks /Create /TN $Task /TR `"$BatCopy`" /SC ONCE /ST $st /RL LIMITED /F /IT"
cmd /c "schtasks /Run /TN $Task"
Start-Sleep -Seconds 22

$py = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match "python" -and $_.CommandLine -match "arise_igris_escudo_btc" })
Write-Host "HOST=$(hostname) PYTHON_IGRIS=$($py.Count)"
foreach ($p in $py) {
  Write-Host "  PID=$($p.ProcessId)"
  Set-Content -Path "$Root\data\arise_igris_escudo.pid" -Value $p.ProcessId
}

Write-Host "=== TAIL ==="
Get-Content $log -Tail 18 -Encoding UTF8
if ((Test-Path $err) -and (Get-Item $err).Length -gt 0) {
  Write-Host "=== ERR ==="
  Get-Content $err -Tail 25 -Encoding UTF8
}

$btc = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  $_.CommandLine -and (
    ($_.CommandLine -match 'arise_beru_rango_manos' -and $_.CommandLine -match '--activo\s+BTC(\s|$)') -or
    ($_.CommandLine -match 'btc_inverso')
  )
}).Count
Write-Host "BTC_BERU_LEFT=$btc"

if ($py.Count -lt 1) { Write-Host "FALLO_SIN_IGRIS"; exit 2 }
Write-Host "OK_SCHTASK_MARKET"
exit 0
