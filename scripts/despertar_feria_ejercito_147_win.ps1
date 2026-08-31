# Despertar ejercito feria lineal completo (lista 147) — lotes escalonados
param(
    [int]$BatchSize = 25,
    [int]$EscalonSegundos = 12,
    [int]$PausaEntreLotes = 8
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$listaPath = Join-Path $Root "data\beru\rango\feria_ejercito_147.txt"
if (-not (Test-Path $listaPath)) {
    Write-Error "Falta $listaPath"
}
$santos = @(
    (Get-Content $listaPath -Raw).Trim() -split "[,\s;]+" |
        ForEach-Object { $_.Trim().ToUpper() } |
        Where-Object { $_ }
) | Sort-Object -Unique

Write-Host "DESPERTAR FERIA EJERCITO: $($santos.Count) Santos" -ForegroundColor Magenta

$lotes = @()
for ($i = 0; $i -lt $santos.Count; $i += $BatchSize) {
    $slice = $santos[$i..([Math]::Min($i + $BatchSize - 1, $santos.Count - 1))]
    $lotes += ,@($slice)
}

$n = 1
foreach ($lot in $lotes) {
    Write-Host ""
    Write-Host "=== LOTE $n / $($lotes.Count) ($($lot.Count) Santos) ===" -ForegroundColor Cyan
    & (Join-Path $Root "scripts\despertar_santos_feria_win.ps1") `
        -Santos ($lot -join ",") `
        -EscalonSegundos $EscalonSegundos `
        -SinOjos
    if ($n -lt $lotes.Count) {
        Start-Sleep -Seconds $PausaEntreLotes
    }
    $n++
}

Write-Host ""
Write-Host "Despertar completo. Correr: python scripts/auditar_feria_doctrina.py" -ForegroundColor Green
