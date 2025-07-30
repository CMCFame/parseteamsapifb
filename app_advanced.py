"""
Aplicación Streamlit con resolver avanzado de fixtures
Usa tokenización inteligente y filtrado de ligas para mejor precisión
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
from advanced_fixture_resolver import AdvancedFixtureResolver
from load_env import load_env_file

# Cargar variables de entorno al inicio
load_env_file()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app_advanced_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Procesador Avanzado de Equipos - API Football",
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

def process_csv_with_advanced_resolver(df: pd.DataFrame, api_key: str) -> Dict:
    """
    Procesa el CSV usando el resolver avanzado de fixtures
    """
    logger.info(f"Iniciando procesamiento avanzado de {len(df)} filas")
    logger.info(f"API Key configurada: {api_key[:10]}...{api_key[-5:]}")
    
    resolver = AdvancedFixtureResolver(api_key)
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
            
            # Procesar con AdvancedFixtureResolver
            logger.info(f"Enviando a AdvancedFixtureResolver: {match_text}")
            result = resolver.process_match_text(match_text)
            logger.info(f"Resultado de AdvancedResolver: success={result.get('success', False)}")
            
            result['row_index'] = i
            result['original_data'] = row.to_dict()
            
            if result['success']:
                successful_matches += 1
                team_ids = result.get('team_ids', {})
                debug_info = result.get('debug_info', {})
                logger.info(f"Éxito - Local: {team_ids.get('home', {}).get('name')} (ID: {team_ids.get('home', {}).get('id')}), "
                           f"Visitante: {team_ids.get('away', {}).get('name')} (ID: {team_ids.get('away', {}).get('id')}), "
                           f"Score: {debug_info.get('score', 'N/A')}")
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
            logger.info(f"Pausando 0.8s antes de la siguiente llamada API")
            time.sleep(0.8)  # Pausa un poco más larga para el resolver avanzado
    
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

def create_excel_with_advanced_results(df_original: pd.DataFrame, processing_results: Dict) -> bytes:
    """
    Crea archivo Excel con resultados del resolver avanzado
    """
    results = processing_results['results']
    
    # Crear DataFrame con resultados
    enhanced_data = []
    mapping_data = []
    
    for result in results:
        row_data = result['original_data'].copy()
        
        if result['success']:
            team_ids = result['team_ids']
            fixture = result['fixture']
            debug_info = result.get('debug_info', {})
            
            # Agregar IDs a los datos originales
            row_data['Local_API_ID'] = team_ids['home']['id']
            row_data['Local_API_Name'] = team_ids['home']['name']
            row_data['Visitante_API_ID'] = team_ids['away']['id']
            row_data['Visitante_API_Name'] = team_ids['away']['name']
            row_data['Fixture_ID'] = fixture['id']
            row_data['Liga_ID'] = fixture['league_id']
            row_data['Liga_Name'] = fixture['league_name']
            row_data['Season'] = fixture['season']
            row_data['Match_Status'] = 'FOUND'
            row_data['Match_Method'] = 'ADVANCED_RESOLVER'
            row_data['Match_Score'] = debug_info.get('score', 0)
            
            # Datos para hoja de mapeo
            mapping_data.append({
                'Fila': result['row_index'] + 1,
                'Local_Original': team_ids['home']['original_name'],
                'Local_API_Name': team_ids['home']['name'],
                'Local_API_ID': team_ids['home']['id'],
                'Visitante_Original': team_ids['away']['original_name'],
                'Visitante_API_Name': team_ids['away']['name'],
                'Visitante_API_ID': team_ids['away']['id'],
                'Fixture_ID': fixture['id'],
                'Liga': fixture['league_name'],
                'Liga_ID': fixture['league_id'],
                'Season': fixture['season'],
                'Match_Score': round(debug_info.get('score', 0), 4),
                'Home_Score': round(debug_info.get('s_home', 0), 3),
                'Away_Score': round(debug_info.get('s_away', 0), 3),
                'Status': 'SUCCESS'
            })
        else:
            # Sin coincidencia
            row_data['Local_API_ID'] = None
            row_data['Local_API_Name'] = 'NOT_FOUND'
            row_data['Visitante_API_ID'] = None
            row_data['Visitante_API_Name'] = 'NOT_FOUND'
            row_data['Fixture_ID'] = None
            row_data['Liga_ID'] = None
            row_data['Liga_Name'] = 'NOT_FOUND'
            row_data['Season'] = None
            row_data['Match_Status'] = 'NOT_FOUND'
            row_data['Match_Method'] = 'ADVANCED_RESOLVER'
            row_data['Match_Score'] = 0
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
                'Fixture_ID': None,
                'Liga': 'NOT_FOUND',
                'Liga_ID': None,
                'Season': None,
                'Match_Score': 0,
                'Home_Score': 0,
                'Away_Score': 0,
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
        mapping_df.to_excel(writer, sheet_name='Mapeo_Avanzado', index=False)
        
        # Hoja de resumen
        summary_data = {
            'Métrica': ['Total de partidos', 'Fixtures encontrados', 'Fixtures no encontrados', 'Tasa de éxito', 'Método usado'],
            'Valor': [
                processing_results['summary']['total'],
                processing_results['summary']['successful'],
                processing_results['summary']['failed'],
                f"{processing_results['summary']['success_rate']:.1f}%",
                'Advanced Resolver con Tokenización'
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumen', index=False)
    
    return output.getvalue()

def main():
    # Título principal
    st.markdown("""
    <div class="main-header">
        <h1>⚽ Procesador AVANZADO de Equipos - API Football</h1>
        <p>Resolver inteligente con tokenización, filtrado de ligas y scoring avanzado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con configuración
    st.sidebar.header("🔧 Configuración Avanzada")
    
    # API Key
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
    
    # Información sobre el método avanzado
    st.sidebar.markdown("""
    ### 🎯 Resolver Avanzado
    
    **Nuevas características:**
    - 🧠 **Tokenización inteligente**: Analiza nombres por tokens
    - 🚫 **Filtro de ligas**: Evita equipos femeniles/juveniles
    - 📊 **Scoring mejorado**: Múltiples factores de coincidencia
    - 🎯 **Normalización**: Maneja acentos y abreviaciones
    - ⚡ **Cache inteligente**: Optimiza llamadas API
    
    **Ligas prioritarias:**
    - Premier League, La Liga, Bundesliga
    - Serie A, Ligue 1, Liga MX, MLS
    - Y más ligas principales automáticamente
    """)
    
    # Sección principal
    st.header("📊 Procesar Archivo CSV")
    
    # Verificar si existe tashist.csv automáticamente
    if os.path.exists('tashist.csv'):
        if st.button("🎯 Procesar tashist.csv con Resolver Avanzado"):
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
            if 'show_advanced_confirmation' not in st.session_state:
                st.session_state.show_advanced_confirmation = False
            if 'advanced_processing_confirmed' not in st.session_state:
                st.session_state.advanced_processing_confirmed = False
            
            # Botón para procesar
            if st.button("🚀 Procesar con Resolver Avanzado", type="primary"):
                logger.info("=== INICIANDO PROCESAMIENTO AVANZADO ===")
                logger.info(f"Total de filas a procesar: {len(df)}")
                logger.info(f"API Key configurada: {api_key is not None}")
                st.session_state.show_advanced_confirmation = True
                logger.info("Mostrando pantalla de confirmación avanzada")
            
            # Mostrar confirmación si el botón fue presionado
            if st.session_state.show_advanced_confirmation:
                st.info(f"🧠 **Iniciando procesamiento con Resolver Avanzado**\n- Total de filas: **{len(df)}**\n- Método: Tokenización + Filtrado de Ligas\n- API Key configurada: ✅")
                
                # Advertencia sobre tiempo y costos
                st.warning(f"⚠️ **Advertencia**: Se realizarán hasta {len(df)} llamadas a la API con el resolver avanzado. "
                          f"Esto puede tomar más tiempo pero dará resultados más precisos.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Confirmar Procesamiento Avanzado", type="primary"):
                        st.session_state.advanced_processing_confirmed = True
                        logger.info("Usuario confirmó procesamiento avanzado")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancelar"):
                        st.session_state.show_advanced_confirmation = False
                        st.session_state.advanced_processing_confirmed = False
                        logger.info("Usuario canceló procesamiento avanzado")
                        st.rerun()
            
            # Ejecutar procesamiento si fue confirmado
            if st.session_state.get('advanced_processing_confirmed', False):
                try:
                    logger.info("INICIANDO PROCESAMIENTO AVANZADO CONFIRMADO")
                    with st.spinner("Procesando con Resolver Avanzado de Fixtures..."):
                        # Procesar con AdvancedFixtureResolver
                        processing_results = process_csv_with_advanced_resolver(df, api_key)
                        
                        # Resetear estados después del procesamiento
                        st.session_state.show_advanced_confirmation = False
                        st.session_state.advanced_processing_confirmed = False
                        
                        # Mostrar resultados
                        st.header("📈 Resultados del Procesamiento Avanzado")
                        
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
                            st.subheader("✅ Fixtures Encontrados (Resolver Avanzado)")
                            
                            success_data = []
                            for result in successful_results[:15]:  # Mostrar más resultados
                                team_ids = result['team_ids']
                                fixture = result['fixture']
                                debug_info = result.get('debug_info', {})
                                
                                success_data.append({
                                    'Partido Original': result['original_text'],
                                    'Local': f"{team_ids['home']['name']} (ID: {team_ids['home']['id']})",
                                    'Visitante': f"{team_ids['away']['name']} (ID: {team_ids['away']['id']})",
                                    'Liga': f"{fixture['league_name']} ({fixture['season']})",
                                    'Score': f"{debug_info.get('score', 0):.3f}",
                                    'Fecha': result['match_info']['date']
                                })
                            
                            st.dataframe(pd.DataFrame(success_data), use_container_width=True)
                            
                            if len(successful_results) > 15:
                                st.write(f"... y {len(successful_results) - 15} resultados más")
                        
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
                        st.header("💾 Descargar Resultados Avanzados")
                        
                        try:
                            excel_data = create_excel_with_advanced_results(df, processing_results)
                            
                            st.download_button(
                                label="📥 Descargar Excel con Resultados Avanzados",
                                data=excel_data,
                                file_name="equipos_resolver_avanzado.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                            # Descargar resultados JSON
                            results_json = json.dumps(processing_results, indent=2, ensure_ascii=False, default=str)
                            st.download_button(
                                label="📥 Descargar Resultados JSON",
                                data=results_json,
                                file_name="resultados_resolver_avanzado.json",
                                mime="application/json"
                            )
                            
                            st.markdown("""
                            <div class="success-box">
                            <h4>🎉 ¡Procesamiento Avanzado Completado!</h4>
                            <p>El archivo Excel incluye tres hojas:</p>
                            <ul>
                                <li><strong>Datos_con_IDs:</strong> Datos originales + IDs de API Football + Info de Liga</li>
                                <li><strong>Mapeo_Avanzado:</strong> Mapeo detallado con scores de coincidencia</li>
                                <li><strong>Resumen:</strong> Estadísticas del procesamiento avanzado</li>
                            </ul>
                            <p><strong>🔥 Características del Resolver Avanzado:</strong></p>
                            <ul>
                                <li>🧠 <strong>Tokenización Inteligente:</strong> Analiza nombres por componentes</li>
                                <li>🚫 <strong>Filtrado Automático:</strong> Evita equipos juveniles y femeniles</li>
                                <li>📊 <strong>Scoring Detallado:</strong> Múltiples factores de coincidencia</li>
                                <li>🎯 <strong>Mayor Precisión:</strong> Mejor identificación de equipos principales</li>
                            </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            logger.error(f"Error creando archivo Excel: {str(e)}")
                            st.error(f"❌ Error creando archivo Excel: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error durante el procesamiento avanzado: {str(e)}")
                    st.error(f"❌ Error durante el procesamiento avanzado: {str(e)}")
                    with st.expander("🔍 Detalles del error"):
                        st.code(str(e))
                    # Resetear estados en caso de error
                    st.session_state.show_advanced_confirmation = False
                    st.session_state.advanced_processing_confirmed = False
        
        except Exception as e:
            st.error(f"❌ Error procesando el archivo: {str(e)}")
    
    # Información adicional
    with st.expander("ℹ️ ¿Cómo funciona el Resolver Avanzado?"):
        st.markdown("""
        ### 📖 Proceso del Resolver Avanzado
        
        1. **🧠 Tokenización Inteligente**: Divide nombres de equipos en componentes (tokens)
        
        2. **🎯 Normalización Avanzada**: 
           - Elimina acentos (América → America)
           - Expande abreviaciones (Man City → Manchester City)
           - Aplica alias conocidos automáticamente
        
        3. **🚫 Filtrado de Ligas**:
           - Bloquea ligas femeniles, juveniles (U23, U21, etc.)
           - Prioriza ligas principales conocidas
           - Evita equipos reserva y academias
        
        4. **📊 Scoring Inteligente**:
           - Jaccard similarity entre tokens
           - Bonificación por coincidencias exactas
           - Bonificación por prefijos/substrings
           - Penalty por diferencia temporal
        
        5. **⏰ Ventana Temporal**: Busca partidos en ±90 minutos de la hora especificada
        
        ### 🎯 Ventajas vs Método Anterior
        
        - **🎯 Mayor Precisión**: Tokenización vs matching simple de strings
        - **🚫 Menos Falsos Positivos**: Filtrado automático de equipos juveniles
        - **🧠 Más Inteligente**: Maneja variaciones de nombres automáticamente
        - **📊 Transparente**: Scores detallados para debugging
        - **⚡ Optimizado**: Cache inteligente reduce llamadas API
        
        ### 📝 Formato de Entrada
        
        Mismo formato que antes:
        ```
        Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa
        ```
        
        Pero ahora con **mucha mejor precisión** en los resultados.
        """)

if __name__ == "__main__":
    main()