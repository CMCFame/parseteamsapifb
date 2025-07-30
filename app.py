import streamlit as st
import pandas as pd
import json
import requests
import time
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional
import io
import base64

# Configuración de la página
st.set_page_config(
    page_title="Procesador de Equipos - API Football",
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

class TeamAssociationSystem:
    """Sistema de asociación de equipos simplificado para Streamlit"""
    
    def __init__(self):
        self.manual_mappings = self._create_manual_mappings()
    
    def _create_manual_mappings(self) -> Dict[str, str]:
        """Mapeo manual para casos problemáticos conocidos"""
        return {
            # Liga MX
            "ÁGUILAS": "América",
            "AGUILAS": "América", 
            "AMERICA": "América",
            "América": "América",
            "C. AZUL": "Cruz Azul",
            "C AZUL": "Cruz Azul",
            "PUMAS": "Pumas UNAM",
            "TIJUANA": "Club Tijuana",
            "MAZATLAN": "Mazatlán FC",
            "MAZATLÁN": "Mazatlán FC",
            "LEON": "León",
            "LEÓN": "León",
            "QUERETARO": "Querétaro",
            "PUEBLA": "Puebla",
            "TOLUCA": "Toluca",
            "PACHUCA": "Pachuca",
            "TIGRES": "Tigres UNAM",
            "MONTERREY": "Monterrey",
            "ATLAS": "Atlas",
            "NECAXA": "Necaxa",
            "JUAREZ": "FC Juárez",
            "JUÁREZ": "FC Juárez",
            "SAN LUIS": "Atlético San Luis",
            "GUADALAJARA": "Guadalajara",
            
            # Premier League
            "Man City": "Manchester City",
            "Man United": "Manchester United",
            "Man Utd": "Manchester United",
            "C. Palace": "Crystal Palace",
            "Crystal Palace": "Crystal Palace",
            "Brighton": "Brighton & Hove Albion",
            "Wolves": "Wolverhampton Wanderers",
            "Wolverhamp": "Wolverhampton Wanderers",
            "Newcastle": "Newcastle United",
            "West Ham": "West Ham United",
            "Arsenal": "Arsenal",
            "Liverpool": "Liverpool",
            "Chelsea": "Chelsea",
            "Tottenham": "Tottenham Hotspur",
            "Nottingham": "Nottingham Forest",
            "Aston Villa": "Aston Villa",
            "Everton": "Everton",
            "Brentford": "Brentford",
            "Fulham": "Fulham",
            "Bournemouth": "AFC Bournemouth",
            
            # La Liga
            "Real Madrid": "Real Madrid",
            "Barcelona": "FC Barcelona",
            "Atlético Madrid": "Atletico Madrid",
            "Sevilla": "Sevilla",
            "Valencia": "Valencia",
            "Ath Bilbao": "Athletic Bilbao",
            "Athletic": "Athletic Bilbao",
            "Betis": "Real Betis",
            "R. Sociedad": "Real Sociedad",
            "Las Palmas": "UD Las Palmas",
            "Celta": "Celta Vigo",
            "Rayo Vallecano": "Rayo Vallecano",
            "Villarreal": "Villarreal",
            "Osasuna": "CA Osasuna",
            "Espanyol": "Espanyol",
            "Girona": "Girona",
            "Alavés": "Deportivo Alaves",
            "Getafe": "Getafe",
            
            # MLS
            "LA Galaxy": "LA Galaxy",
            "LAFC": "Los Angeles FC",
            "LOS ÁNGELES": "Los Angeles FC",
            "Inter Miami": "Inter Miami CF",
            "MIAMI": "Inter Miami CF",
            "Austin": "Austin FC",
            "NY City": "New York City FC",
            "NYCFC": "New York City FC",
            "NYC FC": "New York City FC",
            "NY Red Bulls": "New York Red Bulls",
            "NY RBULLS": "New York Red Bulls",
            "NY R BULLS": "New York Red Bulls",
            "FILADELFIA": "Philadelphia Union",
            "Philadelphia": "Philadelphia Union",
            "Charlotte": "Charlotte FC",
            "Seattle": "Seattle Sounders FC",
            "Portland": "Portland Timbers",
            "Salt Lake": "Real Salt Lake",
            "San Jose": "San Jose Earthquakes",
            "SAN JOSÉ": "San Jose Earthquakes",
            "Kansas City": "Sporting Kansas City",
            "Columbus": "Columbus Crew",
            "Colorado": "Colorado Rapids",
            "Dallas": "FC Dallas",
            "Houston": "Houston Dynamo FC",
            "Chicago": "Chicago Fire FC",
            "Cincinnati": "FC Cincinnati",
            "Nashville": "Nashville SC",
            "Minnesota": "Minnesota United FC",
            "Orlando": "Orlando City SC",
            "DC United": "D.C. United",
            "Toronto": "Toronto FC",
            "Montreal": "CF Montréal",
            "Vancouver": "Vancouver Whitecaps FC",
            "St. Louis": "St. Louis City SC",
            
            # Serie A
            "Inter": "Inter Milan",
            "AC Milan": "AC Milan",
            "Milan": "AC Milan",
            "Juventus": "Juventus",
            "Roma": "AS Roma",
            "Lazio": "Lazio",
            "Napoli": "Napoli",
            "Atalanta": "Atalanta",
            "Fiorentina": "Fiorentina",
            "Bologna": "Bologna",
            "Genoa": "Genoa",
            "Lecce": "Lecce",
            "Empoli": "Empoli",
            "Cagliari": "Cagliari",
            "Como": "Como",
            "Verona": "Hellas Verona",
            "Parma": "Parma",
            "Udinese": "Udinese",
            
            # Bundesliga
            "B MUNICH": "Bayern Munich",
            "B Munich": "Bayern Munich",
            "Dortmund": "Borussia Dortmund",
            "Leverkusen": "Bayer Leverkusen",
            "Leipzig": "RB Leipzig",
            "Stuttgart": "VfB Stuttgart",
            "Frankfurt": "Eintracht Frankfurt",
            "Friburgo": "SC Freiburg",
            "Wolfsburgo": "VfL Wolfsburg",
            "Union Berlin": "1. FC Union Berlin",
            "W Bremen": "Werder Bremen",
            "W. Bremen": "Werder Bremen",
            "H. Kiel": "Holstein Kiel",
            "St Pauli": "FC St. Pauli",
            "Mainz": "1. FSV Mainz 05",
            
            # Otros
            "PSG": "Paris Saint Germain",
            "PARÍS S.G.": "Paris Saint Germain",
            "Marseille": "Olympique Marseille",
            "Marsella": "Olympique Marseille",
            "Ajax": "Ajax",
            "PSV": "PSV Eindhoven",
            "Feyenoord": "Feyenoord",
            "AZ Alkmaar": "AZ Alkmaar",
        }
    
    def normalize_name(self, name: str) -> str:
        """Normaliza el nombre del equipo"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        common_words = ['fc', 'cf', 'club', 'de', 'del', 'la', 'el', 'los', 'las']
        words = normalized.split()
        filtered_words = [w for w in words if w not in common_words]
        
        return ' '.join(filtered_words) if filtered_words else normalized
    
    def calculate_similarity(self, team1: str, team2: str) -> float:
        """Calcula similaridad entre dos nombres"""
        norm1 = self.normalize_name(team1)
        norm2 = self.normalize_name(team2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def find_best_match(self, team_name: str, api_teams: List[Dict]) -> Optional[Dict]:
        """Encuentra la mejor coincidencia"""
        
        # 1. Revisar mapeo manual primero
        if team_name in self.manual_mappings:
            mapped_name = self.manual_mappings[team_name]
            for api_team in api_teams:
                if self.normalize_name(mapped_name) == self.normalize_name(api_team.get('name', '')):
                    return {
                        'api_team': api_team,
                        'confidence': 1.0,
                        'method': 'manual_mapping'
                    }
        
        # 2. Búsqueda por similaridad
        best_match = None
        best_score = 0
        
        for api_team in api_teams:
            api_name = api_team.get('name', '')
            
            # Coincidencia exacta normalizada
            if self.normalize_name(team_name) == self.normalize_name(api_name):
                return {
                    'api_team': api_team,
                    'confidence': 1.0,
                    'method': 'exact_match'
                }
            
            # Similaridad de cadena
            similarity = self.calculate_similarity(team_name, api_name)
            
            # Coincidencia de contenido
            norm_team = self.normalize_name(team_name)
            norm_api = self.normalize_name(api_name)
            
            if norm_team in norm_api or norm_api in norm_team:
                similarity += 0.3
            
            if similarity > best_score and similarity >= 0.6:
                best_score = similarity
                best_match = {
                    'api_team': api_team,
                    'confidence': similarity,
                    'method': 'similarity'
                }
        
        return best_match

def crear_datos_equipos_ejemplo():
    """Crea datos de ejemplo para demostración"""
    return [
        {"id": 1, "name": "Real Madrid", "code": "REA", "country": "Spain"},
        {"id": 2, "name": "FC Barcelona", "code": "BAR", "country": "Spain"},
        {"id": 3, "name": "Manchester City", "code": "MCI", "country": "England"},
        {"id": 4, "name": "Liverpool", "code": "LIV", "country": "England"},
        {"id": 5, "name": "Bayern Munich", "code": "BAY", "country": "Germany"},
        {"id": 6, "name": "Chelsea", "code": "CHE", "country": "England"},
        {"id": 7, "name": "Arsenal", "code": "ARS", "country": "England"},
        {"id": 8, "name": "Atletico Madrid", "code": "ATM", "country": "Spain"},
        {"id": 9, "name": "Inter Milan", "code": "INT", "country": "Italy"},
        {"id": 10, "name": "AC Milan", "code": "MIL", "country": "Italy"},
        {"id": 541, "name": "América", "code": "AME", "country": "Mexico"},
        {"id": 1032, "name": "Cruz Azul", "code": "CRU", "country": "Mexico"},
        {"id": 1040, "name": "Pumas UNAM", "code": "PUM", "country": "Mexico"},
        {"id": 1044, "name": "Tigres UNAM", "code": "TIG", "country": "Mexico"},
        {"id": 1046, "name": "Monterrey", "code": "MTY", "country": "Mexico"},
        {"id": 1050, "name": "Guadalajara", "code": "GDL", "country": "Mexico"},
        {"id": 1052, "name": "Atlas", "code": "ATL", "country": "Mexico"},
        {"id": 1054, "name": "Pachuca", "code": "PAC", "country": "Mexico"},
        {"id": 1056, "name": "León", "code": "LEO", "country": "Mexico"},
        {"id": 1058, "name": "Toluca", "code": "TOL", "country": "Mexico"},
        {"id": 1323, "name": "LA Galaxy", "code": "LAG", "country": "USA"},
        {"id": 1324, "name": "Inter Miami CF", "code": "MIA", "country": "USA"},
        {"id": 1325, "name": "New York City FC", "code": "NYC", "country": "USA"},
        {"id": 1326, "name": "Seattle Sounders FC", "code": "SEA", "country": "USA"},
        {"id": 1327, "name": "Los Angeles FC", "code": "LAF", "country": "USA"},
    ]

def obtener_equipos_desde_api(api_key: str, league_ids: List[int]) -> List[Dict]:
    """Obtiene equipos desde API Football"""
    
    headers = {
        'x-rapidapi-host': 'v3.football.api-sports.io',
        'x-rapidapi-key': api_key
    }
    
    all_teams = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, league_id in enumerate(league_ids):
        status_text.text(f"Obteniendo equipos de liga {league_id}...")
        
        url = "https://v3.football.api-sports.io/teams"
        params = {'league': league_id, 'season': 2024}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                teams = data.get('response', [])
                
                for item in teams:
                    team = item.get('team', {})
                    if team:
                        all_teams.append({
                            'id': team.get('id'),
                            'name': team.get('name'),
                            'code': team.get('code'),
                            'country': team.get('country'),
                            'logo': team.get('logo')
                        })
                
                status_text.text(f"✅ Liga {league_id}: {len(teams)} equipos obtenidos")
            else:
                status_text.text(f"❌ Error en liga {league_id}: {response.status_code}")
                
        except Exception as e:
            status_text.text(f"❌ Error en liga {league_id}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(league_ids))
        time.sleep(0.5)  # Pausa para respetar límites de API
    
    status_text.text(f"✅ Total: {len(all_teams)} equipos obtenidos")
    return all_teams

def extraer_equipos_del_excel(df: pd.DataFrame) -> List[str]:
    """Extrae equipos únicos del DataFrame"""
    
    all_teams = set()
    team_columns = ['Local', 'Visitante', 'Local_1', 'Visitante_1']
    
    for column in team_columns:
        if column in df.columns:
            teams = df[column].dropna().astype(str).str.strip()
            teams = teams[teams != '']
            all_teams.update(teams)
    
    return sorted(list(all_teams))

def procesar_equipos(teams_list: List[str], api_teams: List[Dict]) -> Dict:
    """Procesa la lista de equipos y encuentra coincidencias"""
    
    association_system = TeamAssociationSystem()
    results = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, team in enumerate(teams_list):
        status_text.text(f"Procesando: {team}")
        match = association_system.find_best_match(team, api_teams)
        results[team] = match
        progress_bar.progress((i + 1) / len(teams_list))
    
    status_text.text("✅ Procesamiento completado")
    return results

def generar_reporte(results: Dict) -> Dict:
    """Genera reporte de resultados"""
    
    successful = []
    low_confidence = []
    no_matches = []
    
    for team_name, result in results.items():
        if result is None:
            no_matches.append(team_name)
        elif result['confidence'] >= 0.9:
            successful.append({
                'original': team_name,
                'matched': result['api_team']['name'],
                'id': result['api_team']['id'],
                'confidence': result['confidence'],
                'method': result['method']
            })
        else:
            low_confidence.append({
                'original': team_name,
                'matched': result['api_team']['name'],
                'id': result['api_team']['id'],
                'confidence': result['confidence'],
                'method': result['method']
            })
    
    return {
        'successful_matches': successful,
        'low_confidence_matches': low_confidence,
        'no_matches': no_matches
    }

def crear_excel_con_ids(df_original: pd.DataFrame, results: Dict) -> bytes:
    """Crea archivo Excel con IDs de API Football"""
    
    # Crear mapeo de nombres a IDs
    team_mapping = {}
    for team_name, result in results.items():
        if result and result.get('api_team'):
            team_mapping[team_name] = result['api_team']['id']
        else:
            team_mapping[team_name] = None
    
    # Agregar columnas de IDs
    df_result = df_original.copy()
    df_result['Local_API_ID'] = df_result['Local'].map(team_mapping)
    df_result['Visitante_API_ID'] = df_result['Visitante'].map(team_mapping)
    
    if 'Local_1' in df_result.columns:
        df_result['Local_1_API_ID'] = df_result['Local_1'].map(team_mapping)
    if 'Visitante_1' in df_result.columns:
        df_result['Visitante_1_API_ID'] = df_result['Visitante_1'].map(team_mapping)
    
    # Crear DataFrame de mapeo
    mapping_data = []
    for team_name, result in results.items():
        if result:
            mapping_data.append({
                'Equipo_Original': team_name,
                'API_Football_ID': result['api_team']['id'],
                'API_Football_Name': result['api_team']['name'],
                'Confidence': result['confidence'],
                'Method': result['method'],
                'Country': result['api_team'].get('country', 'N/A')
            })
        else:
            mapping_data.append({
                'Equipo_Original': team_name,
                'API_Football_ID': None,
                'API_Football_Name': 'NO ENCONTRADO',
                'Confidence': 0,
                'Method': 'none',
                'Country': 'N/A'
            })
    
    mapping_df = pd.DataFrame(mapping_data)
    
    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_result.to_excel(writer, sheet_name='Datos_con_IDs', index=False)
        mapping_df.to_excel(writer, sheet_name='Mapeo_Equipos', index=False)
    
    return output.getvalue()

# INTERFAZ PRINCIPAL
def main():
    # Título principal
    st.markdown("""
    <div class="main-header">
        <h1>⚽ Procesador de Equipos - API Football</h1>
        <p>Asocia automáticamente los equipos de tu Excel con los IDs de API Football</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con configuración
    st.sidebar.header("🔧 Configuración")
    
    # Opción de fuente de datos
    data_source = st.sidebar.radio(
        "¿Cómo quieres obtener los datos de equipos?",
        ["📄 Usar datos de ejemplo (demo)", "🌐 Conectar a API Football", "📁 Subir archivo JSON"]
    )
    
    api_teams = []
    
    # Configurar fuente de datos
    if data_source == "📄 Usar datos de ejemplo (demo)":
        st.sidebar.success("✅ Usando datos de ejemplo")
        api_teams = crear_datos_equipos_ejemplo()
        
    elif data_source == "🌐 Conectar a API Football":
        api_key = st.sidebar.text_input(
            "🔑 API Key de API Football",
            type="password",
            help="Obtén tu API key en https://www.api-football.com/"
        )
        
        if api_key:
            # Selección de ligas
            st.sidebar.subheader("🏆 Selecciona las ligas")
            
            ligas_disponibles = {
                "39": "Premier League (Inglaterra)",
                "140": "La Liga (España)",
                "78": "Bundesliga (Alemania)",
                "135": "Serie A (Italia)",
                "61": "Ligue 1 (Francia)",
                "262": "Liga MX (México)",
                "253": "MLS (Estados Unidos)",
                "71": "Brasileirão (Brasil)",
                "128": "Primera División (Argentina)"
            }
            
            selected_leagues = []
            for league_id, league_name in ligas_disponibles.items():
                if st.sidebar.checkbox(league_name, value=(league_id in ["39", "140", "262", "253"])):
                    selected_leagues.append(int(league_id))
            
            if st.sidebar.button("🔄 Cargar equipos desde API"):
                if selected_leagues:
                    with st.spinner("Obteniendo equipos desde API Football..."):
                        api_teams = obtener_equipos_desde_api(api_key, selected_leagues)
                        st.sidebar.success(f"✅ {len(api_teams)} equipos cargados")
                        st.session_state['api_teams'] = api_teams
                else:
                    st.sidebar.error("❌ Selecciona al menos una liga")
        
        # Usar equipos cargados previamente
        if 'api_teams' in st.session_state:
            api_teams = st.session_state['api_teams']
            
    elif data_source == "📁 Subir archivo JSON":
        uploaded_json = st.sidebar.file_uploader(
            "📁 Sube tu archivo JSON con datos de API Football",
            type=['json']
        )
        
        if uploaded_json:
            try:
                api_teams = json.load(uploaded_json)
                st.sidebar.success(f"✅ {len(api_teams)} equipos cargados desde JSON")
            except Exception as e:
                st.sidebar.error(f"❌ Error al cargar JSON: {str(e)}")
    
    # Sección principal
    st.header("📊 Procesar Archivo Excel")
    
    if not api_teams:
        st.warning("⚠️ Primero configura la fuente de datos de equipos en el panel lateral")
        return
    
    # Subir archivo Excel
    uploaded_file = st.file_uploader(
        "📁 Sube tu archivo Excel con los equipos",
        type=['xlsx', 'xls'],
        help="Asegúrate de que tu archivo tenga columnas con nombres de equipos (Local, Visitante, etc.)"
    )
    
    if uploaded_file:
        try:
            # Leer archivo Excel
            df = pd.read_excel(uploaded_file, sheet_name=0)
            
            st.success(f"✅ Archivo cargado: {len(df)} filas encontradas")
            
            # Mostrar vista previa
            with st.expander("👁️ Ver vista previa del archivo"):
                st.dataframe(df.head(10))
            
            # Extraer equipos
            teams_list = extraer_equipos_del_excel(df)
            
            st.info(f"🔍 Encontrados **{len(teams_list)}** equipos únicos")
            
            # Mostrar algunos equipos encontrados
            with st.expander("📋 Ver equipos encontrados"):
                cols = st.columns(3)
                for i, team in enumerate(teams_list[:15]):
                    cols[i % 3].write(f"• {team}")
                if len(teams_list) > 15:
                    st.write(f"... y {len(teams_list) - 15} equipos más")
            
            # Botón para procesar
            if st.button("🚀 Procesar Equipos", type="primary"):
                with st.spinner("Procesando equipos..."):
                    # Procesar equipos
                    results = procesar_equipos(teams_list, api_teams)
                    
                    # Generar reporte
                    report = generar_reporte(results)
                    
                    # Mostrar resultados
                    st.header("📈 Resultados del Procesamiento")
                    
                    # Métricas
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "✅ Exitosos",
                            len(report['successful_matches']),
                            f"{len(report['successful_matches'])/len(teams_list)*100:.1f}%"
                        )
                    
                    with col2:
                        st.metric(
                            "⚠️ Baja Confianza",
                            len(report['low_confidence_matches']),
                            f"{len(report['low_confidence_matches'])/len(teams_list)*100:.1f}%"
                        )
                    
                    with col3:
                        st.metric(
                            "❌ Sin Coincidencias",
                            len(report['no_matches']),
                            f"{len(report['no_matches'])/len(teams_list)*100:.1f}%"
                        )
                    
                    with col4:
                        st.metric(
                            "📊 Total Equipos",
                            len(teams_list)
                        )
                    
                    # Coincidencias exitosas
                    if report['successful_matches']:
                        st.subheader("✅ Coincidencias Exitosas")
                        successful_df = pd.DataFrame(report['successful_matches'])
                        st.dataframe(successful_df, use_container_width=True)
                    
                    # Coincidencias de baja confianza
                    if report['low_confidence_matches']:
                        st.subheader("⚠️ Coincidencias de Baja Confianza (Revisar)")
                        low_conf_df = pd.DataFrame(report['low_confidence_matches'])
                        st.dataframe(low_conf_df, use_container_width=True)
                        
                        st.markdown("""
                        <div class="warning-box">
                        <strong>⚠️ Atención:</strong> Estas coincidencias tienen baja confianza. 
                        Revísalas manualmente antes de usar los IDs.
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Sin coincidencias
                    if report['no_matches']:
                        st.subheader("❌ Equipos Sin Coincidencias")
                        st.write("Estos equipos no pudieron ser asociados automáticamente:")
                        
                        cols = st.columns(3)
                        for i, team in enumerate(report['no_matches']):
                            cols[i % 3].write(f"• {team}")
                    
                    # Crear y descargar archivo Excel
                    st.header("💾 Descargar Resultados")
                    
                    excel_data = crear_excel_con_ids(df, results)
                    
                    st.download_button(
                        label="📥 Descargar Excel con IDs",
                        data=excel_data,
                        file_name="equipos_con_api_ids.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Descargar resultados JSON
                    results_json = json.dumps(results, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 Descargar Resultados JSON",
                        data=results_json,
                        file_name="resultados_asociacion.json",
                        mime="application/json"
                    )
                    
                    st.markdown("""
                    <div class="success-box">
                    <h4>🎉 ¡Procesamiento Completado!</h4>
                    <p>Descarga el archivo Excel para ver tus datos originales con las nuevas columnas de IDs de API Football.</p>
                    <p>El archivo incluye dos hojas:</p>
                    <ul>
                        <li><strong>Datos_con_IDs:</strong> Tus datos originales + columnas de IDs</li>
                        <li><strong>Mapeo_Equipos:</strong> Tabla completa de asociaciones</li>
                    </ul>
                    </div>
                    """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
    
    # Información adicional
    with st.expander("ℹ️ ¿Cómo usar esta aplicación?"):
        st.markdown("""
        ### 📖 Instrucciones de Uso
        
        1. **Configura la fuente de datos** en el panel lateral:
           - **Datos de ejemplo**: Para probar la aplicación
           - **API Football**: Conecta con tu API key para datos reales
           - **Archivo JSON**: Si ya tienes datos de API Football
        
        2. **Sube tu archivo Excel** con los nombres de equipos
        
        3. **Haz clic en "Procesar Equipos"** y espera los resultados
        
        4. **Revisa los resultados** especialmente las coincidencias de baja confianza
        
        5. **Descarga el archivo Excel** con los IDs de API Football incluidos
        
        ### 🎯 Tipos de Coincidencias
        
        - **✅ Exitosas (>90%)**: Coincidencias muy confiables, úsalas directamente
        - **⚠️ Baja Confianza (60-90%)**: Revisa manualmente antes de usar
        - **❌ Sin Coincidencias**: Requieren búsqueda manual o mapeo adicional
        
        ### 🔑 API Key de API Football
        
        Para obtener datos reales, necesitas una cuenta en [API-Football.com](https://www.api-football.com/)
        La versión gratuita incluye 100 llamadas por día.
        """)

if __name__ == "__main__":
    main()