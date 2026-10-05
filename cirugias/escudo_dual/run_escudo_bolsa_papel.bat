@echo off
cd /d C:\Users\lenovo\ShadowHarmy
set IGRIS_BOLSA_LOG_SOLO_STDOUT=1
set IGRIS_BOLSA_LIVE_OK=1
"C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u scripts\arise_igris_escudo_bolsa.py --vivo --intervalo 15 1>> data\logs\arise_igris_escudo_bolsa_out.log 2>>&1
