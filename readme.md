# ⚽ Procesador de Equipos - API Football

Una aplicación web que permite asociar automáticamente los nombres de equipos de fútbol de tu archivo Excel con los IDs oficiales de API Football.

## 🌟 Características

- **Interfaz web amigable** - No necesitas instalar nada en tu computadora
- **Mapeo inteligente** - Sistema multi-criterio para encontrar coincidencias precisas
- **Múltiples fuentes de datos** - Usa datos de ejemplo, API en vivo, o tu archivo JSON
- **Resultados categorizados** - Identifica coincidencias exitosas, de baja confianza, y sin match
- **Descarga inmediata** - Obtén tu Excel con los IDs de API Football incluidos

## 📊 Ligas Soportadas

- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (Inglaterra)
- 🇪🇸 La Liga (España)
- 🇩🇪 Bundesliga (Alemania)
- 🇮🇹 Serie A (Italia)
- 🇫🇷 Ligue 1 (Francia)
- 🇲🇽 Liga MX (México)
- 🇺🇸 MLS (Estados Unidos)
- 🇧🇷 Brasileirão (Brasil)
- 🇦🇷 Primera División (Argentina)

## 🚀 Uso

1. Abre la aplicación web
2. Configura tu fuente de datos (ejemplo, API, o JSON)
3. Sube tu archivo Excel
4. Procesa los equipos
5. Descarga los resultados

## 📁 Formato de Archivo Excel

Tu archivo debe tener columnas con nombres de equipos, como:
- `Local`
- `Visitante`
- `Local_1`
- `Visitante_1`

## 🎯 Tipos de Coincidencias

- **✅ Exitosas (>90%)**: Muy confiables, úsalas directamente
- **⚠️ Baja Confianza (60-90%)**: Revisa manualmente
- **❌ Sin Coincidencias**: Requieren búsqueda manual

## 🔑 API Football

Para datos reales, obtén tu API key gratuita en [API-Football.com](https://www.api-football.com/)

## 📝 Ejemplo de Uso

El sistema puede asociar automáticamente:
- "ÁGUILAS" → América (ID: 541)
- "Man City" → Manchester City (ID: 50)
- "B MUNICH" → Bayern Munich (ID: 157)
- "C. AZUL" → Cruz Azul (ID: 1032)

## 💾 Archivos de Salida

- **Excel con IDs**: Tu archivo original + columnas de IDs de API Football
- **Hoja de Mapeo**: Tabla completa de todas las asociaciones
- **JSON de Resultados**: Datos detallados para uso técnico