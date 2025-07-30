"""
Sistema de matching basado en fixtures de API Football
Usa el endpoint headtohead para encontrar partidos específicos
"""

import requests
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

class FixtureMatcher:
    """Sistema para encontrar equipos usando fixtures específicos de API Football"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
        }
        self.cache = {}  # Cache para evitar llamadas repetidas
    
    def parse_match_text(self, match_text: str) -> Optional[Dict]:
        """
        Extrae información del partido desde el texto
        Ejemplo: "Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa"
        """
        try:
            # Patrón para extraer fecha y equipos
            pattern = r"Fecha:\s*(\d+/\d+)\s*(\d+:\d+)?,\s*Partido:\s*(.+?)\s*vs\s*(.+)"
            match = re.search(pattern, match_text)
            
            if match:
                date_part = match.group(1)  # "4/4"
                time_part = match.group(2)  # "21:00"
                team1 = match.group(3).strip()  # "Tijuana"
                team2 = match.group(4).strip()  # "Necaxa"
                
                # Convertir fecha a formato más completo (asumiendo año actual)
                current_year = datetime.now().year
                if "/" in date_part:
                    month, day = date_part.split("/")
                    parsed_date = f"{current_year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    parsed_date = None
                
                return {
                    'date': parsed_date,
                    'time': time_part,
                    'team1': team1,
                    'team2': team2,
                    'original_text': match_text
                }
        except Exception as e:
            print(f"Error parsing match text '{match_text}': {e}")
        
        return None
    
    def search_fixture_by_teams(self, team1: str, team2: str, date: str = None) -> Optional[Dict]:
        """
        Busca fixture usando nombres de equipos
        Nota: Este método requiere que conozcamos los IDs de los equipos
        """
        # Este método es un placeholder para búsqueda por nombres
        # En la práctica, necesitaríamos primero obtener los IDs de los equipos
        print(f"Búsqueda por nombres no implementada directamente. Necesitamos IDs de equipos.")
        return None
    
    def search_fixtures_by_date(self, date: str) -> List[Dict]:
        """
        Busca todos los fixtures en una fecha específica
        """
        cache_key = f"fixtures_{date}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        querystring = {"date": date}
        
        try:
            response = requests.get(url, headers=self.headers, params=querystring, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])
                self.cache[cache_key] = fixtures
                return fixtures
            else:
                print(f"Error API: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error buscando fixtures por fecha {date}: {e}")
            return []
    
    def find_matching_fixture(self, match_info: Dict) -> Optional[Dict]:
        """
        Encuentra el fixture que coincide con la información del partido
        """
        if not match_info or not match_info.get('date'):
            return None
        
        team1 = match_info['team1'].lower().strip()
        team2 = match_info['team2'].lower().strip()
        target_date = match_info['date']
        
        # Buscar fixtures en la fecha
        fixtures = self.search_fixtures_by_date(target_date)
        
        if not fixtures:
            print(f"No se encontraron fixtures para la fecha {target_date}")
            return None
        
        print(f"Encontrados {len(fixtures)} fixtures para {target_date}")
        
        # Buscar coincidencias por nombre de equipo
        best_match = None
        best_score = 0
        
        for fixture in fixtures:
            try:
                home_team = fixture.get('teams', {}).get('home', {}).get('name', '').lower()
                away_team = fixture.get('teams', {}).get('away', {}).get('name', '').lower()
                
                # Calcular score de coincidencia
                score = 0
                
                # Verificar si los nombres de equipos están contenidos
                if (team1 in home_team or home_team in team1) and (team2 in away_team or away_team in team2):
                    score = 2
                elif (team1 in away_team or away_team in team1) and (team2 in home_team or home_team in team2):
                    score = 2
                elif team1 in home_team or team1 in away_team or team2 in home_team or team2 in away_team:
                    score = 1
                
                if score > best_score:
                    best_score = score
                    best_match = fixture
                    
            except Exception as e:
                print(f"Error procesando fixture: {e}")
                continue
        
        if best_match and best_score >= 1:
            print(f"Fixture encontrado: {best_match.get('teams', {}).get('home', {}).get('name')} vs {best_match.get('teams', {}).get('away', {}).get('name')}")
            return best_match
        
        return None
    
    def extract_team_ids(self, fixture: Dict) -> Tuple[Optional[int], Optional[int]]:
        """
        Extrae los IDs de los equipos de un fixture
        """
        try:
            home_id = fixture.get('teams', {}).get('home', {}).get('id')
            away_id = fixture.get('teams', {}).get('away', {}).get('id')
            return home_id, away_id
        except Exception as e:
            print(f"Error extrayendo IDs de equipos: {e}")
            return None, None
    
    def process_match_text(self, match_text: str) -> Dict:
        """
        Procesa un texto de partido completo y retorna información de equipos
        """
        # Parsear información del partido
        match_info = self.parse_match_text(match_text)
        
        if not match_info:
            return {
                'success': False,
                'error': 'No se pudo parsear el texto del partido',
                'original_text': match_text
            }
        
        # Buscar fixture correspondiente
        fixture = self.find_matching_fixture(match_info)
        
        if not fixture:
            return {
                'success': False,
                'error': 'No se encontró fixture correspondiente',
                'match_info': match_info,
                'original_text': match_text
            }
        
        # Extraer IDs de equipos
        home_id, away_id = self.extract_team_ids(fixture)
        
        return {
            'success': True,
            'match_info': match_info,
            'fixture': fixture,
            'team_ids': {
                'home': {
                    'id': home_id,
                    'name': fixture.get('teams', {}).get('home', {}).get('name'),
                    'original_name': match_info['team1']
                },
                'away': {
                    'id': away_id,
                    'name': fixture.get('teams', {}).get('away', {}).get('name'),
                    'original_name': match_info['team2']
                }
            },
            'original_text': match_text
        }

def test_fixture_matcher():
    """Función de prueba para el FixtureMatcher"""
    api_key = "d4b4999861mshc077d4879aba6d4p19f6e7jsn1bc73c757992"
    matcher = FixtureMatcher(api_key)
    
    # Casos de prueba
    test_cases = [
        "Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa",
        "Fecha: 4/5 8:00, Partido: Crystal Palace vs Brighton",
        "Fecha: 4/5 17:00, Partido: Pachuca vs América"
    ]
    
    print("=== Pruebas de FixtureMatcher ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Prueba {i+1} ---")
        print(f"Texto: {test_case}")
        
        result = matcher.process_match_text(test_case)
        
        if result['success']:
            print("Exito!")
            team_ids = result['team_ids']
            print(f"Equipo Local: {team_ids['home']['name']} (ID: {team_ids['home']['id']})")
            print(f"Equipo Visitante: {team_ids['away']['name']} (ID: {team_ids['away']['id']})")
        else:
            print(f"Error: {result['error']}")
        
        # Pausa entre llamadas para respetar límites de API
        time.sleep(1)

if __name__ == "__main__":
    test_fixture_matcher()