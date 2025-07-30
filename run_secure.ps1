# Script seguro para ejecutar la aplicación con variables de entorno
Write-Host "🔐 Cargando configuración segura..." -ForegroundColor Green

# Cambiar al directorio del proyecto
Set-Location "C:\Users\victo\OneDrive\Documents\GitHub\parseteamsapifb"

# Verificar que existe el archivo .env
if (Test-Path ".env") {
    Write-Host "✅ Configuración de API encontrada" -ForegroundColor Green
} else {
    Write-Host "❌ Archivo .env no encontrado. Crea uno con tu API key:" -ForegroundColor Red
    Write-Host "RAPIDAPI_KEY=tu_api_key_aqui" -ForegroundColor Yellow
    exit 1
}

# Cargar variables de entorno desde .env
Write-Host "📂 Cargando variables de entorno..." -ForegroundColor Cyan
python load_env.py

Write-Host "🚀 Iniciando aplicación..." -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

# Ejecutar la aplicación
python -m streamlit run app_fixed.py

Write-Host "Aplicación cerrada." -ForegroundColor Red