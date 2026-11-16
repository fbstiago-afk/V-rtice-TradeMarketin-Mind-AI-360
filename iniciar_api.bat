@echo off
REM Inicia a API local do TradeMind AI 360 (modo demo para o visual de chat do Power BI Desktop)
cd /d "%~dp0"
where python >nul 2>nul || (echo Python nao encontrado. Instale Python 3.10+ em python.org & pause & exit /b 1)
python -c "import pandas, sklearn" 2>nul || python -m pip install pandas scikit-learn
set TRADEMIND_DEMO=1
python 04_API\api.py
pause
