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
import os
from pathlib import Path

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
    
    def find_best_match(self, team_name: str, api_teams: List[Dict], context: List[Dict] = None) -> Optional[Dict]:
        """Encuentra la mejor coincidencia usando información contextual"""
        
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
        
        # 2. Búsqueda mejorada con contexto
        candidates = []
        
        for api_team in api_teams:
            api_name = api_team.get('name', '')
            
            # Coincidencia exacta normalizada
            if self.normalize_name(team_name) == self.normalize_name(api_name):
                return {
                    'api_team': api_team,
                    'confidence': 1.0,
                    'method': 'exact_match'
                }
            
            # Calcular similaridad base
            similarity = self.calculate_similarity(team_name, api_name)
            
            # Coincidencia de contenido
            norm_team = self.normalize_name(team_name)
            norm_api = self.normalize_name(api_name)
            
            if norm_team in norm_api or norm_api in norm_team:
                similarity += 0.2
            
            # Boost por contexto si está disponible
            context_boost = 0
            if context and len(context) > 0:
                context_boost = self.calculate_context_boost(team_name, api_team, context, api_teams)
                similarity += context_boost
            
            if similarity >= 0.5:  # Umbral más bajo para considerar candidatos
                candidates.append({
                    'api_team': api_team,
                    'confidence': similarity,
                    'context_boost': context_boost,
                    'method': 'contextual_similarity' if context_boost > 0 else 'similarity'
                })
        
        # Ordenar candidatos por confianza
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Retornar el mejor candidato si supera el umbral mínimo
        if candidates and candidates[0]['confidence'] >= 0.6:
            return candidates[0]
        
        return None
    
    def calculate_context_boost(self, team_name: str, api_team: Dict, context: List[Dict], all_api_teams: List[Dict]) -> float:
        """Calcula boost de confianza basado en contexto de partidos"""
        
        boost = 0
        opponent_matches = 0
        total_opponents = 0
        
        for match_info in context:
            opponent = match_info.get('opponent', '')
            if not opponent:
                continue
                
            total_opponents += 1
            
            # Buscar si el oponente también está en la misma liga/competición
            opponent_country = None
            for api_opp in all_api_teams:
                if (self.normalize_name(opponent) == self.normalize_name(api_opp.get('name', '')) or
                    self.calculate_similarity(opponent, api_opp.get('name', '')) > 0.8):
                    opponent_country = api_opp.get('country', '')
                    break
            
            # Si encontramos el país del oponente y coincide con nuestro equipo candidato
            if opponent_country and opponent_country == api_team.get('country', ''):
                opponent_matches += 1
        
        # Calcular boost basado en coincidencias de país con oponentes
        if total_opponents > 0:
            country_match_ratio = opponent_matches / total_opponents
            boost += country_match_ratio * 0.3  # Máximo boost de 0.3
        
        # Boost adicional si hay muchos partidos (más datos = más confianza)
        if len(context) >= 3:
            boost += 0.1
        elif len(context) >= 5:
            boost += 0.15
        
        return min(boost, 0.4)  # Limitar boost máximo

def normalizar_json_api_football(raw_data) -> List[Dict]:
    """
    Normaliza diferentes estructuras de JSON de API Football
    
    Maneja estos formatos:
    1. Array directo: [{"id": 1, "name": "Team"}, ...]
    2. Con response: {"response": [{"team": {"id": 1, "name": "Team"}}, ...]}
    3. Con response directo: {"response": [{"id": 1, "name": "Team"}, ...]}
    4. Objeto con teams: {"teams": [...]}
    5. Objeto indexado por ID: {"1553": {"id": 1553, "name": "Team"}, "8047": {...}}
    """
    
    try:
        # Caso 1: Si es un string, parsearlo
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
        
        teams_data = []
        
        # Caso 2: Si tiene clave "response" (formato API Football estándar)
        if isinstance(raw_data, dict) and "response" in raw_data:
            teams_data = raw_data["response"]
            
        # Caso 3: Si tiene clave "teams" 
        elif isinstance(raw_data, dict) and "teams" in raw_data:
            teams_data = raw_data["teams"]
            
        # Caso 4: Si es directamente un array
        elif isinstance(raw_data, list):
            teams_data = raw_data
            
        # Caso 5: Objeto indexado por ID (tu formato)
        elif isinstance(raw_data, dict):
            # Verificar si parece ser un objeto indexado por IDs
            # Las claves deberían ser números (como strings) y los valores objetos con "id"
            sample_keys = list(raw_data.keys())[:5]  # Tomar muestra de claves
            
            if sample_keys and all(key.isdigit() for key in sample_keys):
                # Es un objeto indexado por IDs
                st.info("🔍 Detectado formato: Objeto indexado por IDs de equipos")
                teams_data = list(raw_data.values())
            else:
                # Caso 6: Si es un diccionario con datos directos
                if "id" in raw_data:
                    teams_data = [raw_data]
                else:
                    # Intentar encontrar la lista más grande en el JSON
                    for key, value in raw_data.items():
                        if isinstance(value, list) and len(value) > len(teams_data):
                            teams_data = value
        
        # Normalizar cada equipo
        normalized_teams = []
        
        for item in teams_data:
            # Si el item tiene una estructura {"team": {...}}
            if isinstance(item, dict) and "team" in item:
                team_data = item["team"]
            # Si el item es directamente los datos del equipo
            elif isinstance(item, dict):
                team_data = item
            else:
                continue
            
            # Crear estructura normalizada
            normalized_team = {
                "id": team_data.get("id"),
                "name": team_data.get("name", ""),
                "code": team_data.get("code", ""),
                "country": team_data.get("country", ""),
                "founded": team_data.get("founded"),
                "logo": team_data.get("logo", ""),
                "national": team_data.get("national", False)
            }
            
            # Solo agregar si tiene al menos ID y nombre
            if normalized_team["id"] and normalized_team["name"]:
                normalized_teams.append(normalized_team)
        
        # Mostrar información de debug
        if normalized_teams:
            st.success(f"✅ Estructura detectada y normalizada correctamente")
            st.info(f"📊 {len(normalized_teams)} equipos extraídos del JSON")
            
            # Mostrar estadísticas
            countries = set(team.get("country", "") for team in normalized_teams)
            national_teams = sum(1 for team in normalized_teams if team.get("national", False))
            club_teams = len(normalized_teams) - national_teams
            
            st.write(f"🌍 **Países representados:** {len(countries)}")
            st.write(f"🏴 **Selecciones nacionales:** {national_teams}")
            st.write(f"⚽ **Equipos de clubes:** {club_teams}")
        
        return normalized_teams
        
    except Exception as e:
        st.error(f"Error normalizando JSON: {str(e)}")
        st.write("**Información de debug:**")
        st.write(f"Tipo de datos: {type(raw_data)}")
        if isinstance(raw_data, dict):
            st.write(f"Claves principales: {list(raw_data.keys())[:10]}")
        return []

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
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': api_key
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

def extraer_contexto_partidos(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Extrae información contextual de los partidos para cada equipo"""
    
    team_context = {}
    
    for _, row in df.iterrows():
        local = str(row.get('Local', '')).strip()
        visitante = str(row.get('Visitante', '')).strip()
        match_text = str(row.get('Match text', '')).strip()
        fecha = str(row.get('Fecha', '')).strip()
        
        # Crear contexto del partido
        match_info = {
            'opponent': visitante if local else local,
            'match_text': match_text,
            'fecha': fecha,
            'is_home': True if local else False
        }
        
        # Agregar contexto para el equipo local
        if local and local != '':
            if local not in team_context:
                team_context[local] = []
            match_info_local = match_info.copy()
            match_info_local['opponent'] = visitante
            match_info_local['is_home'] = True
            team_context[local].append(match_info_local)
        
        # Agregar contexto para el equipo visitante
        if visitante and visitante != '':
            if visitante not in team_context:
                team_context[visitante] = []
            match_info_visitante = match_info.copy()
            match_info_visitante['opponent'] = local
            match_info_visitante['is_home'] = False
            team_context[visitante].append(match_info_visitante)
    
    return team_context

def procesar_equipos(teams_list: List[str], api_teams: List[Dict], team_context: Dict[str, List[Dict]] = None) -> Dict:
    """Procesa la lista de equipos y encuentra coincidencias"""
    
    # Validar que api_teams tenga la estructura correcta
    if not api_teams:
        st.error("❌ No hay datos de equipos para procesar")
        return {}
    
    # Verificar estructura del primer equipo
    if api_teams and isinstance(api_teams[0], dict):
        sample_team = api_teams[0]
        required_keys = ['id', 'name']
        missing_keys = [key for key in required_keys if key not in sample_team]
        
        if missing_keys:
            st.error(f"❌ Estructura de JSON incorrecta. Faltan claves: {missing_keys}")
            st.write("**Estructura esperada:**")
            st.json({"id": 123, "name": "Nombre del equipo", "code": "COD", "country": "País"})
            st.write("**Estructura encontrada:**")
            st.json(sample_team)
            return {}
    
    association_system = TeamAssociationSystem()
    results = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for i, team in enumerate(teams_list):
            status_text.text(f"Procesando: {team}")
            
            try:
                context = team_context.get(team, []) if team_context else []
                match = association_system.find_best_match(team, api_teams, context)
                results[team] = match
            except Exception as e:
                st.warning(f"⚠️ Error procesando equipo '{team}': {str(e)}")
                results[team] = None
            
            progress_bar.progress((i + 1) / len(teams_list))
        
        status_text.text("✅ Procesamiento completado")
        return results
        
    except Exception as e:
        status_text.text(f"❌ Error en procesamiento: {str(e)}")
        st.error(f"Error general en procesamiento: {str(e)}")
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
            match_info = {
                'original': team_name,
                'matched': result['api_team']['name'],
                'id': result['api_team']['id'],
                'confidence': result['confidence'],
                'method': result['method'],
                'country': result['api_team'].get('country', 'N/A')
            }
            if 'context_boost' in result:
                match_info['context_boost'] = result['context_boost']
            successful.append(match_info)
        else:
            match_info = {
                'original': team_name,
                'matched': result['api_team']['name'],
                'id': result['api_team']['id'],
                'confidence': result['confidence'],
                'method': result['method'],
                'country': result['api_team'].get('country', 'N/A')
            }
            if 'context_boost' in result:
                match_info['context_boost'] = result['context_boost']
            low_confidence.append(match_info)
    
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
        if 'api_teams' not in st.session_state or len(st.session_state.get('api_teams', [])) < 20:
            st.sidebar.success("✅ Usando datos de ejemplo")
            api_teams = crear_datos_equipos_ejemplo()
            st.session_state['api_teams'] = api_teams
        else:
            api_teams = st.session_state['api_teams']
            st.sidebar.success("✅ Datos de ejemplo cargados")
        
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
                raw_data = json.load(uploaded_json)
                
                # Mostrar información de debug sobre la estructura
                st.sidebar.write("🔍 **Analizando estructura del JSON...**")
                
                # Detectar y normalizar diferentes estructuras de JSON
                api_teams = normalizar_json_api_football(raw_data)
                
                if api_teams:
                    st.session_state['api_teams'] = api_teams
                    st.sidebar.success(f"✅ {len(api_teams)} equipos procesados desde JSON")
                    
                    # Mostrar muestra de los primeros equipos
                    with st.sidebar.expander("👁️ Ver muestra de equipos"):
                        for i, team in enumerate(api_teams[:3]):
                            st.sidebar.write(f"**{i+1}.** {team.get('name', 'Sin nombre')} (ID: {team.get('id', 'N/A')})")
                else:
                    st.sidebar.error("❌ No se pudieron extraer equipos del JSON")
                    
            except json.JSONDecodeError as e:
                st.sidebar.error(f"❌ Error al leer JSON: Archivo no válido")
            except Exception as e:
                st.sidebar.error(f"❌ Error al procesar JSON: {str(e)}")
                # Mostrar más detalles del error
                st.sidebar.write("📝 **Detalles del error:**")
                st.sidebar.code(str(e))
        
        # Usar equipos cargados previamente
        if 'api_teams' in st.session_state:
            api_teams = st.session_state['api_teams']
    
    # Sección principal
    st.header("📊 Procesar Archivo CSV/Excel")
    
    # Verificar si tenemos datos de equipos (ya sea en variable local o en session_state)
    if not api_teams and 'api_teams' not in st.session_state:
        st.warning("⚠️ Primero configura la fuente de datos de equipos en el panel lateral")
        return
    
    # Verificar si existe tashist.csv automáticamente
    tashist_path = Path('tashist.csv')
    if tashist_path.exists() and st.button("🎯 Usar archivo tashist.csv automáticamente"):
        try:
            df = pd.read_csv(tashist_path)
            st.success(f"✅ Archivo tashist.csv cargado automáticamente: {len(df)} filas")
            
            # Procesar automáticamente
            uploaded_file = "auto_loaded"
        except Exception as e:
            st.error(f"❌ Error cargando tashist.csv: {str(e)}")
            uploaded_file = None
    else:
        uploaded_file = None
    
    # Si no tenemos api_teams local pero sí en session_state, usarlos
    if not api_teams and 'api_teams' in st.session_state:
        api_teams = st.session_state['api_teams']
        st.info(f"📊 Usando datos cargados: {len(api_teams)} equipos disponibles")
    
    # Subir archivo Excel/CSV si no se cargó automáticamente
    if not uploaded_file:
        uploaded_file = st.file_uploader(
            "📁 Sube tu archivo Excel/CSV con los equipos",
            type=['xlsx', 'xls', 'csv'],
            help="Asegúrate de que tu archivo tenga columnas con nombres de equipos (Local, Visitante, etc.)"
        )
    
    if uploaded_file:
        try:
            # Leer archivo según tipo
            if uploaded_file == "auto_loaded":
                # Ya está cargado
                pass
            elif uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, sheet_name=0)
            
            st.success(f"✅ Archivo cargado: {len(df)} filas encontradas")
            
            # Mostrar vista previa
            with st.expander("👁️ Ver vista previa del archivo"):
                st.dataframe(df.head(10))
            
            # Extraer equipos y contexto
            teams_list = extraer_equipos_del_excel(df)
            team_context = extraer_contexto_partidos(df)
            
            st.info(f"🔍 Encontrados **{len(teams_list)}** equipos únicos")
            
            # Mostrar información de contexto
            if team_context:
                context_info = []
                for team, matches in team_context.items():
                    context_info.append(f"{team}: {len(matches)} partidos")
                
                with st.expander("🎯 Información contextual extraída"):
                    st.write(f"**Equipos con contexto:** {len(team_context)}")
                    st.write("**Partidos por equipo:**")
                    for info in context_info[:10]:  # Mostrar solo los primeros 10
                        st.write(f"• {info}")
                    if len(context_info) > 10:
                        st.write(f"... y {len(context_info) - 10} equipos más")
            
            # Mostrar algunos equipos encontrados
            with st.expander("📋 Ver equipos encontrados"):
                cols = st.columns(3)
                for i, team in enumerate(teams_list[:15]):
                    cols[i % 3].write(f"• {team}")
                if len(teams_list) > 15:
                    st.write(f"... y {len(teams_list) - 15} equipos más")
            
            # Botón para procesar
            if st.button("🚀 Procesar Equipos", type="primary"):
                
                # Verificar que tenemos datos válidos
                if not api_teams:
                    st.error("❌ No hay datos de equipos cargados. Configura la fuente de datos primero.")
                    return
                
                # Mostrar información sobre los datos que vamos a usar
                st.info(f"📊 **Datos a procesar:**\n- Equipos en Excel: **{len(teams_list)}**\n- Equipos en base de datos: **{len(api_teams)}**")
                
                try:
                    with st.spinner("Procesando equipos con información contextual..."):
                        # Procesar equipos con contexto
                        results = procesar_equipos(teams_list, api_teams, team_context)
                        
                        if not results:
                            st.error("❌ No se pudieron procesar los equipos. Revisa la estructura de tus datos.")
                            return
                        
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
                        
                        try:
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
                            st.error(f"❌ Error creando archivo Excel: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error durante el procesamiento: {str(e)}")
                    st.write("**Detalles del error:**")
                    st.code(str(e))
                    
                    # Información de debug
                    with st.expander("🔍 Información de Debug"):
                        st.write("**Tipo de api_teams:**", type(api_teams))
                        st.write("**Cantidad de equipos:**", len(api_teams) if api_teams else 0)
                        if api_teams and len(api_teams) > 0:
                            st.write("**Estructura del primer equipo:**")
                            st.json(api_teams[0])
        
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