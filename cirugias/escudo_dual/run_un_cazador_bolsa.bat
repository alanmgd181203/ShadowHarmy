@echo off
cd /d C:\Users\lenovo\ShadowHarmy
set BERU_MAR=okx
set BERU_RANGO_PERFIL=piedra
set BERU_RANGO_MANOS=true
set BERU_RANGO_RED_EXPANSIVA=1
set MODO_SIMULACION=false
set PYTHONUTF8=1
if not exist "data\beru\rango\%1" mkdir "data\beru\rango\%1"
"C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u scripts\arise_beru_rango_manos.py --activo %1 --perfil piedra --manos-go --continuar 1>> "data\beru\rango\%1\manos_piedra_stdout.log" 2>>&1
