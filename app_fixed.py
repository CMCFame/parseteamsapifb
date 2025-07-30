"""
Aplicación Streamlit mejorada que usa fixtures de API Football
para obtener IDs de equipos de manera precisa - VERSIÓN CORREGIDA
"""

import streamlit as st
import pandas as pd
import json
import time
from typing import Dict, List
import io
import logging
import sys
import os
from fixture_matcher import FixtureMatcher
from load_env import load_env_file

# Cargar variables de entorno al inicio
load_env_file()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Procesador de Equipos - API Football (Fixture-Based)",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def process_csv_with_fixtures(df: pd.DataFrame, api_key: str) -> Dict:
    """
    Procesa el CSV usando fixtures de API Football
    """
    logger.info(f"Iniciando procesamiento de {len(df)} filas")
    logger.info(f"API Key configurada: {api_key[:10]}...{api_key[-5:]}")
    
    matcher = FixtureMatcher(api_key)
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_rows = len(df)
    successful_matches = 0
    failed_matches = 0
    
    logger.info(f"Columnas disponibles en DataFrame: {list(df.columns)}")

    for i, row in df.iterrows():
        try:
            match_text = str(row.get('Match text', '')).strip()
            logger.info(f"Procesando fila {i+1}: {match_text}")
            
            if not match_text or match_text == 'nan':
                logger.warning(f"Fila {i+1}: Sin texto de partido válido")
                results.append({
                    'row_index': i,
                    'success': False,
                    'error': 'Sin texto de partido',
                    'original_data': row.to_dict()
                })
                failed_matches += 1
                continue
            
            status_text.text(f"Procesando fila {i+1}/{total_rows}: {match_text}")
            
            # Procesar con FixtureMatcher
            logger.info(f"Enviando a FixtureMatcher: {match_text}")
            result = matcher.process_match_text(match_text)
            logger.info(f"Resultado de FixtureMatcher: success={result.get('success', False)}")
            
            result['row_index'] = i
            result['original_data'] = row.to_dict()
            
            if result['success']:
                successful_matches += 1
                team_ids = result.get('team_ids', {})
                logger.info(f"Éxito - Local: {team_ids.get('home', {}).get('name')} (ID: {team_ids.get('home', {}).get('id')}), Visitante: {team_ids.get('away', {}).get('name')} (ID: {team_ids.get('away', {}).get('id')})")
            else:
                failed_matches += 1
                logger.error(f"Error en fila {i+1}: {result.get('error', 'Error desconocido')}")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Excepción en fila {i+1}: {str(e)}")
            results.append({
                'row_index': i,
                'success': False,
                'error': f'Error procesando fila: {str(e)}',
                'original_data': row.to_dict()
            })
            failed_matches += 1
        
        progress_bar.progress((i + 1) / total_rows)
        
        # Pausa para respetar límites de API
        if i < total_rows - 1:  # No pausar en la última iteración
            logger.info(f"Pausando 0.5s antes de la siguiente llamada API")
            time.sleep(0.5)
    
    status_text.text(f"Completado: {successful_matches} exitosos, {failed_matches} fallidos")
    logger.info(f"PROCESAMIENTO COMPLETADO - Exitosos: {successful_matches}, Fallidos: {failed_matches}")
    
    return {
        'results': results,
        'summary': {
            'total': total_rows,
            'successful': successful_matches,
            'failed': failed_matches,
            'success_rate': (successful_matches / total_rows * 100) if total_rows > 0 else 0
        }
    }

def create_excel_with_fixture_ids(df_original: pd.DataFrame, processing_results: Dict) -> bytes:
    """
    Crea archivo Excel con IDs obtenidos de fixtures
    """
    results = processing_results['results']
    
    # Crear DataFrame con resultados
    enhanced_data = []
    mapping_data = []
    
    for result in results:
        row_data = result['original_data'].copy()
        
        if result['success']:
            team_ids = result['team_ids']
            
            # Agregar IDs a los datos originales
            row_data['Local_API_ID'] = team_ids['home']['id']
            row_data['Local_API_Name'] = team_ids['home']['name']
            row_data['Visitante_API_ID'] = team_ids['away']['id']
            row_data['Visitante_API_Name'] = team_ids['away']['name']
            row_data['Match_Status'] = 'FOUND'
            row_data['Match_Method'] = 'FIXTURE_BASED'
            
            # Datos para hoja de mapeo
            mapping_data.append({
                'Fila': result['row_index'] + 1,
                'Local_Original': team_ids['home']['original_name'],
                'Local_API_Name': team_ids['home']['name'],
                'Local_API_ID': team_ids['home']['id'],
                'Visitante_Original': team_ids['away']['original_name'],
                'Visitante_API_Name': team_ids['away']['name'],
                'Visitante_API_ID': team_ids['away']['id'],
                'Fecha_Fixture': result['match_info']['date'],
                'Status': 'SUCCESS'
            })
        else:
            # Sin coincidencia
            row_data['Local_API_ID'] = None
            row_data['Local_API_Name'] = 'NOT_FOUND'
            row_data['Visitante_API_ID'] = None
            row_data['Visitante_API_Name'] = 'NOT_FOUND'
            row_data['Match_Status'] = 'NOT_FOUND'
            row_data['Match_Method'] = 'FIXTURE_BASED'
            row_data['Error'] = result.get('error', 'Unknown error')
            
            # Datos para hoja de mapeo
            mapping_data.append({
                'Fila': result['row_index'] + 1,
                'Local_Original': result['original_data'].get('Local', 'N/A'),
                'Local_API_Name': 'NOT_FOUND',
                'Local_API_ID': None,
                'Visitante_Original': result['original_data'].get('Visitante', 'N/A'),
                'Visitante_API_Name': 'NOT_FOUND',
                'Visitante_API_ID': None,
                'Fecha_Fixture': 'N/A',
                'Status': 'FAILED',
                'Error': result.get('error', '')
            })
        
        enhanced_data.append(row_data)
    
    # Crear DataFrames
    enhanced_df = pd.DataFrame(enhanced_data)
    mapping_df = pd.DataFrame(mapping_data)
    
    # Crear archivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        enhanced_df.to_excel(writer, sheet_name='Datos_con_IDs', index=False)
        mapping_df.to_excel(writer, sheet_name='Mapeo_Fixtures', index=False)
        
        # Hoja de resumen
        summary_data = {
            'Métrica': ['Total de partidos', 'Fixtures encontrados', 'Fixtures no encontrados', 'Tasa de éxito'],
            'Valor': [
                processing_results['summary']['total'],
                processing_results['summary']['successful'],
                processing_results['summary']['failed'],
                f"{processing_results['summary']['success_rate']:.1f}%"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumen', index=False)
    
    return output.getvalue()

def main():
    # Título principal
    st.markdown("""
    <div class="main-header">
        <h1>⚽ Procesador de Equipos - API Football (Fixture-Based)</h1>
        <p>Obtén IDs de equipos usando fixtures específicos de API Football</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con configuración
    st.sidebar.header("🔧 Configuración")
    
    # API Key
    # Intentar cargar desde variable de entorno primero
    default_api_key = os.getenv('RAPIDAPI_KEY', '')
    
    api_key = st.sidebar.text_input(
        "🔑 API Key de RapidAPI",
        value=default_api_key,
        type="password",
        help="Tu API key de RapidAPI para API Football. También puedes configurarla como variable de entorno RAPIDAPI_KEY"
    )
    
    if not api_key:
        st.warning("⚠️ Ingresa tu API key para continuar")
        return
    
    # Información sobre el método
    st.sidebar.markdown("""
    ### 🎯 Método Fixture-Based
    
    Este método es más preciso porque:
    - Busca fixtures específicos por fecha
    - Hace matching exacto de partidos
    - Obtiene IDs directamente de API Football
    - Evita ambigüedades de nombres
    """)
    
    # Sección principal
    st.header("📊 Procesar Archivo CSV")
    
    # Verificar si existe tashist.csv automáticamente
    import os
    if os.path.exists('tashist.csv'):
        if st.button("🎯 Procesar tashist.csv automáticamente"):
            try:
                df = pd.read_csv('tashist.csv')
                uploaded_file = "auto_loaded"
            except Exception as e:
                st.error(f"❌ Error cargando tashist.csv: {str(e)}")
                uploaded_file = None
        else:
            uploaded_file = None
    else:
        uploaded_file = None
    
    # Subir archivo si no se cargó automáticamente
    if not uploaded_file:
        uploaded_file = st.file_uploader(
            "📁 Sube tu archivo CSV",
            type=['csv'],
            help="Debe tener una columna 'Match text' con formato: 'Fecha: 4/4 21:00, Partido: Equipo1 vs Equipo2'"
        )
    
    if uploaded_file:
        try:
            # Leer archivo
            if uploaded_file == "auto_loaded":
                # Ya está cargado
                pass
            else:
                df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ Archivo cargado: {len(df)} filas")
            
            # Verificar columnas requeridas
            required_columns = ['Match text']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Faltan columnas requeridas: {missing_columns}")
                st.write("Columnas disponibles:", list(df.columns))
                return
            
            # Mostrar vista previa
            with st.expander("👁️ Vista previa del archivo"):
                st.dataframe(df.head(10))
            
            # Mostrar algunos ejemplos de Match text
            with st.expander("📋 Ejemplos de Match text"):
                match_texts = df['Match text'].dropna().head(10)
                for i, text in enumerate(match_texts):
                    st.write(f"{i+1}. {text}")
            
            # Inicializar estado de sesión
            if 'show_confirmation' not in st.session_state:
                st.session_state.show_confirmation = False
            if 'processing_confirmed' not in st.session_state:
                st.session_state.processing_confirmed = False
            
            # Botón para procesar
            if st.button("🚀 Procesar con API Football", type="primary"):
                logger.info("=== INICIANDO PROCESAMIENTO ===")
                logger.info(f"Total de filas a procesar: {len(df)}")
                logger.info(f"API Key configurada: {api_key is not None}")
                st.session_state.show_confirmation = True
                logger.info("Mostrando pantalla de confirmación")
            
            # Mostrar confirmación si el botón fue presionado
            if st.session_state.show_confirmation:
                st.info(f"📊 **Iniciando procesamiento fixture-based**\n- Total de filas: **{len(df)}**\n- API Key configurada: ✅")
                
                # Advertencia sobre tiempo y costos
                st.warning(f"⚠️ **Advertencia**: Se realizarán hasta {len(df)} llamadas a la API. "
                          f"Esto puede tomar varios minutos y consumir créditos de API.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Confirmar procesamiento", type="primary"):
                        st.session_state.processing_confirmed = True
                        logger.info("Usuario confirmó procesamiento")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancelar"):
                        st.session_state.show_confirmation = False
                        st.session_state.processing_confirmed = False
                        logger.info("Usuario canceló procesamiento")
                        st.rerun()
            
            # Ejecutar procesamiento si fue confirmado
            if st.session_state.get('processing_confirmed', False):
                try:
                    logger.info("INICIANDO PROCESAMIENTO CONFIRMADO")
                    with st.spinner("Procesando fixtures con API Football..."):
                        # Procesar con FixtureMatcher
                        processing_results = process_csv_with_fixtures(df, api_key)
                        
                        # Resetear estados después del procesamiento
                        st.session_state.show_confirmation = False
                        st.session_state.processing_confirmed = False
                        
                        # Mostrar resultados
                        st.header("📈 Resultados del Procesamiento")
                        
                        # Métricas
                        summary = processing_results['summary']
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("📊 Total", summary['total'])
                        
                        with col2:
                            st.metric("✅ Exitosos", summary['successful'], 
                                    f"{summary['success_rate']:.1f}%")
                        
                        with col3:
                            st.metric("❌ Fallidos", summary['failed'])
                        
                        with col4:
                            st.metric("🎯 Precisión", f"{summary['success_rate']:.1f}%")
                        
                        # Mostrar detalles de resultados exitosos
                        successful_results = [r for r in processing_results['results'] if r['success']]
                        if successful_results:
                            st.subheader("✅ Fixtures Encontrados")
                            
                            success_data = []
                            for result in successful_results[:10]:  # Mostrar solo los primeros 10
                                team_ids = result['team_ids']
                                success_data.append({
                                    'Partido Original': result['original_text'],
                                    'Local': f"{team_ids['home']['name']} (ID: {team_ids['home']['id']})",
                                    'Visitante': f"{team_ids['away']['name']} (ID: {team_ids['away']['id']})",
                                    'Fecha': result['match_info']['date']
                                })
                            
                            st.dataframe(pd.DataFrame(success_data), use_container_width=True)
                            
                            if len(successful_results) > 10:
                                st.write(f"... y {len(successful_results) - 10} resultados más")
                        
                        # Mostrar errores si los hay
                        failed_results = [r for r in processing_results['results'] if not r['success']]
                        if failed_results:
                            st.subheader("❌ Partidos No Encontrados")
                            
                            error_data = []
                            for result in failed_results[:10]:
                                error_data.append({
                                    'Partido Original': result.get('original_text', 'N/A'),
                                    'Error': result.get('error', 'Unknown error')
                                })
                            
                            st.dataframe(pd.DataFrame(error_data), use_container_width=True)
                        
                        # Crear y descargar archivo Excel
                        st.header("💾 Descargar Resultados")
                        
                        try:
                            excel_data = create_excel_with_fixture_ids(df, processing_results)
                            
                            st.download_button(
                                label="📥 Descargar Excel con IDs de Fixtures",
                                data=excel_data,
                                file_name="equipos_fixture_based.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                            # Descargar resultados JSON
                            results_json = json.dumps(processing_results, indent=2, ensure_ascii=False, default=str)
                            st.download_button(
                                label="📥 Descargar Resultados JSON",
                                data=results_json,
                                file_name="resultados_fixture_based.json",
                                mime="application/json"
                            )
                            
                            st.markdown("""
                            <div class="success-box">
                            <h4>🎉 ¡Procesamiento Completado!</h4>
                            <p>El archivo Excel incluye tres hojas:</p>
                            <ul>
                                <li><strong>Datos_con_IDs:</strong> Datos originales + IDs de API Football</li>
                                <li><strong>Mapeo_Fixtures:</strong> Mapeo detallado de cada fixture</li>
                                <li><strong>Resumen:</strong> Estadísticas del procesamiento</li>
                            </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            logger.error(f"Error creando archivo Excel: {str(e)}")
                            st.error(f"❌ Error creando archivo Excel: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error durante el procesamiento: {str(e)}")
                    st.error(f"❌ Error durante el procesamiento: {str(e)}")
                    with st.expander("🔍 Detalles del error"):
                        st.code(str(e))
                    # Resetear estados en caso de error
                    st.session_state.show_confirmation = False
                    st.session_state.processing_confirmed = False
        
        except Exception as e:
            st.error(f"❌ Error procesando el archivo: {str(e)}")
    
    # Información adicional
    with st.expander("ℹ️ ¿Cómo funciona el método Fixture-Based?"):
        st.markdown("""
        ### 📖 Proceso Fixture-Based
        
        1. **Parseo del texto**: Extrae fecha, hora y nombres de equipos de la columna "Match text"
        
        2. **Búsqueda por fecha**: Obtiene todos los fixtures de API Football para esa fecha específica
        
        3. **Matching inteligente**: Compara nombres de equipos con los fixtures encontrados
        
        4. **Extracción de IDs**: Obtiene los IDs oficiales directamente del fixture encontrado
        
        ### 🎯 Ventajas
        
        - **Alta precisión**: Encuentra fixtures específicos, no aproximaciones
        - **IDs correctos**: Obtiene IDs directamente de API Football
        - **Manejo de variantes**: Funciona con diferentes formatos de nombres
        - **Verificación por fecha**: Confirma que el partido existe en esa fecha
        
        ### 📝 Formato Requerido
        
        La columna "Match text" debe tener este formato:
        ```
        Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa
        ```
        
        - Fecha en formato M/D o MM/DD
        - Hora opcional
        - Nombres de equipos separados por "vs"
        """)

if __name__ == "__main__":
    main()