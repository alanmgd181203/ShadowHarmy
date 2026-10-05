@echo off
cd /d C:\Users\lenovo\ShadowHarmy
set BERU_MAR=okx
set MODO_SIMULACION=false
set PYTHONUTF8=1
if not exist "data\logs" mkdir "data\logs"
"C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u scripts\vigilar_neto_telegram.py 1>> "data\logs\neto_telegram.log" 2>>&1
