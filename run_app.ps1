# Script de PowerShell para ejecutar la aplicación con logging visible
Write-Host "Iniciando aplicación con logging detallado..." -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener la aplicación" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

# Cambiar al directorio del proyecto
Set-Location "C:\Users\victo\OneDrive\Documents\GitHub\parseteamsapifb"

# Ejecutar la aplicación con logging
python -m streamlit run app_fixture_based.py --logger.level=info

Write-Host "Aplicación cerrada." -ForegroundColor Red