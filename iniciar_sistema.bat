@echo off
title Biofood Nutrition - Control de Inventario
echo ======================================================
echo    Iniciando Servidor Biofood Nutrition...
echo ======================================================

cd /d "%~dp0"
start http://localhost:8501
call .venv\Scripts\activate.bat
streamlit run app.py --server.headless true