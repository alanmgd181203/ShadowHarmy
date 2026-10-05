@echo off
cd /d C:\Users\lenovo\ShadowHarmy
set BERU_MAR=okx
set MODO_SIMULACION=false
set PYTHONUTF8=1
if not exist "data\logs" mkdir "data\logs"
"C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u scripts\vigilar_palanca_okx.py 1>> "data\logs\palanca_okx.log" 2>>&1
