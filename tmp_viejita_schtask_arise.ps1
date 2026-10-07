$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Bat = "C:\Users\lenovo\tmp_arise_igris_viejita.bat"
$Task = "ShadowHarmy_AriseIgrisEscudo"

# Matar TODOS los arise_igris (evitar doble mano)
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -and $_.CommandLine -match "arise_igris_escudo_btc" } |
  ForEach-Object {
    Write-Host "STOP $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
Start-Sleep -Seconds 2

# Limpiar log viejo corrupto
$log = Join-Path $Root "data\logs\arise_igris_escudo_out.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Set-Content -Path $log -Value "" -Encoding utf8

cmd /c "schtasks /Delete /TN $Task /F >nul 2>&1"
# Hora ST unos minutos en el futuro para evitar warning; igual /Run inmediato
$st = (Get-Date).AddMinutes(2).ToString("HH:mm")
cmd /c "schtasks /Create /TN $Task /TR `"$Bat`" /SC ONCE /ST $st /RL LIMITED /F /IT" | Write-Host
cmd /c "schtasks /Run /TN $Task" | Write-Host
Start-Sleep -Seconds 18

$py = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match "python" -and $_.CommandLine -match "arise_igris_escudo_btc" })
Write-Host "HOST=$(hostname) PYTHON_IGRIS=$($py.Count)"
foreach ($p in $py) { Write-Host "  PID=$($p.ProcessId)" }

if ($py.Count -eq 0) {
  Write-Host "FALLBACK hidden unico"
  $env:PYTHONIOENCODING = "utf-8"
  $env:BERU_MAR = "okx"
  $env:IGRIS_ESCUDO_BTC_ACTIVO = "1"
  $env:IGRIS_ESCUDO_BTC_MODO = "live"
  $env:IGRIS_ESCUDO_BTC_LIVE_OK = "1"
  $env:IGRIS_ESCUDO_BTC_R = "dinamico"
  $env:IGRIS_ESCUDO_BTC_FRENTE = "inverso"
  $p2 = Start-Process -FilePath "python" -ArgumentList @("-u","scripts\arise_igris_escudo_btc.py","--intervalo","45") `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru
  Start-Sleep -Seconds 6
  $py = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "python" -and $_.CommandLine -match "arise_igris_escudo_btc" })
  Write-Host "FALLBACK PYTHON_IGRIS=$($py.Count) startPID=$($p2.Id)"
}

if ($py.Count -gt 1) {
  # dejar solo el mas reciente
  $keep = ($py | Sort-Object ProcessId -Descending | Select-Object -First 1)
  foreach ($p in $py) {
    if ($p.ProcessId -ne $keep.ProcessId) {
      Write-Host "KILL_EXTRA $($p.ProcessId)"
      Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
  }
  $py = @($keep)
}

if ($py.Count -lt 1) { Write-Host "FALLO"; exit 2 }
Set-Content -Path "$Root\data\arise_igris_escudo.pid" -Value $py[0].ProcessId
Write-Host "OK_UNICO PID=$($py[0].ProcessId)"
exit 0
