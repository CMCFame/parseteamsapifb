# 🔐 Configuración Segura de API Keys

## ⚠️ IMPORTANTE: Nunca subas tu API key al repositorio

### 1. Configuración de Variables de Entorno

#### Opción A: Archivo .env (Recomendado para desarrollo local)
```bash
# Crea un archivo .env en la raíz del proyecto
RAPIDAPI_KEY=tu_api_key_aqui
```

#### Opción B: Variables de entorno del sistema (Windows)
```powershell
# PowerShell
$env:RAPIDAPI_KEY="tu_api_key_aqui"

# O permanentemente
[Environment]::SetEnvironmentVariable("RAPIDAPI_KEY", "tu_api_key_aqui", "User")
```

#### Opción C: Variables de entorno del sistema (Linux/Mac)
```bash
# Temporal
export RAPIDAPI_KEY="tu_api_key_aqui"

# Permanente (en ~/.bashrc o ~/.zshrc)
echo 'export RAPIDAPI_KEY="tu_api_key_aqui"' >> ~/.bashrc
```

### 2. Ejecución Segura

#### Usar el script PowerShell (Windows)
```powershell
.\run_secure.ps1
```

#### Ejecución manual
```bash
# Cargar variables de entorno
python load_env.py

# Ejecutar aplicación
streamlit run app_fixed.py
```

### 3. Obtener tu API Key

1. Ve a [RapidAPI - API Football](https://rapidapi.com/api-sports/api/api-football/)
2. Registrate/Inicia sesión
3. Suscríbete al plan gratuito (100 llamadas/día)
4. Copia tu API key desde el dashboard
5. Configúrala usando una de las opciones arriba

### 4. Archivos Protegidos

El `.gitignore` protege estos archivos sensibles:
- `.env` - Variables de entorno
- `*.log` - Archivos de log que pueden contener datos sensibles
- `*_fixture_based.xlsx` - Archivos generados que pueden contener datos

### 5. Verificación de Seguridad

Antes de hacer commit:
```bash
# Verificar que no hay API keys en el código
git log --oneline -S "d4b4999861msh" -- "*.py"

# Verificar archivos que se van a subir
git status
```

### 6. Si accidentalmente subes una API key:

1. **Regenera inmediatamente** tu API key en RapidAPI
2. Actualiza tu archivo `.env` local
3. Usa `git filter-branch` o BFG para limpiar el historial
4. Fuerza un push: `git push --force-with-lease`

## 🔍 Verificar Configuración

Ejecuta este comando para verificar que tu API key está configurada:
```python
python -c "import os; print('API Key configurada:', 'RAPIDAPI_KEY' in os.environ)"
```