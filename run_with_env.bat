@echo off
echo 🔐 Cargando configuración segura...
cd /d "C:\Users\victo\OneDrive\Documents\GitHub\parseteamsapifb"

echo 📂 Verificando archivo .env...
if not exist .env (
    echo ❌ Archivo .env no encontrado
    echo Crea uno con: RAPIDAPI_KEY=tu_api_key_aqui
    pause
    exit /b 1
)

echo ✅ Configuración encontrada
echo 🚀 Iniciando aplicación con variables de entorno...
echo Presiona Ctrl+C para detener
echo ================================================

python -c "from load_env import load_env_file; load_env_file()" && python -m streamlit run app_fixed.py

echo Aplicación cerrada.
pause