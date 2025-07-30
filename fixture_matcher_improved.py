"""
Sistema de matching basado en fixtures de API Football - VERSIÓN MEJORADA
Prioriza equipos principales sobre equipos juveniles/reservas
"""

import requests
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import logging

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

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
        logger.info(f"Parseando texto: {match_text}")
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
                
                result = {
                    'date': parsed_date,
                    'time': time_part,
                    'team1': team1,
                    'team2': team2,
                    'original_text': match_text
                }
                logger.info(f"Parseo exitoso: {result}")
                return result
        except Exception as e:
            logger.error(f"Error parsing match text '{match_text}': {e}")
        
        return None
    
    def search_fixture_by_teams(self, team1: str, team2: str, date: str = None) -> Optional[Dict]:
        """
        Busca fixture usando nombres de equipos
        Nota: Este método es un placeholder para búsqueda por nombres
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
            logger.info(f"Buscando fixtures para fecha: {date}")
            response = requests.get(url, headers=self.headers, params=querystring, timeout=10)
            logger.info(f"Respuesta API: status={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])
                logger.info(f"Fixtures encontrados: {len(fixtures)}")
                self.cache[cache_key] = fixtures
                return fixtures
            else:
                logger.error(f"Error API: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error buscando fixtures por fecha {date}: {e}")
            return []
    
    def is_youth_or_reserve_team(self, team_name: str) -> bool:
        """
        Identifica si un equipo es juvenil, reserva o sub-categoría
        """
        team_lower = team_name.lower()
        youth_indicators = [
            'u23', 'u-23', 'sub 23', 'sub-23',
            'u21', 'u-21', 'sub 21', 'sub-21',
            'u20', 'u-20', 'sub 20', 'sub-20',
            'u19', 'u-19', 'sub 19', 'sub-19',
            'u18', 'u-18', 'sub 18', 'sub-18',
            'ii', ' ii ', ' b ', ' b',
            'reserve', 'reserves', 'reserva', 'reservas',
            'youth', 'juvenil', 'juveniles',
            'academy', 'academia',
            'development', 'desarrollo',
            'segunda', '2nd', 'second',
            'filial', 'cantera'
        ]
        
        return any(indicator in team_lower for indicator in youth_indicators)
    
    def calculate_team_priority(self, team_name: str) -> int:
        """
        Calcula prioridad del equipo (mayor número = mayor prioridad)
        """
        if self.is_youth_or_reserve_team(team_name):
            return 1  # Baja prioridad para equipos juveniles
        return 10  # Alta prioridad para equipos principales
    
    def calculate_match_score(self, team1: str, team2: str, home_team: str, away_team: str) -> float:
        """
        Calcula score de coincidencia mejorado
        """
        team1_lower = team1.lower().strip()
        team2_lower = team2.lower().strip()
        home_lower = home_team.lower().strip()
        away_lower = away_team.lower().strip()
        
        score = 0.0
        
        # Puntuación base por coincidencia de nombres
        if (team1_lower in home_lower or home_lower in team1_lower) and (team2_lower in away_lower or away_lower in team2_lower):
            score = 2.0  # Coincidencia exacta en orden correcto
        elif (team1_lower in away_lower or away_lower in team1_lower) and (team2_lower in home_lower or home_lower in team2_lower):
            score = 1.8  # Coincidencia exacta en orden inverso
        elif team1_lower in home_lower or team1_lower in away_lower or team2_lower in home_lower or team2_lower in away_lower:
            score = 1.0  # Coincidencia parcial
        
        # Bonus por prioridad de equipos (equipos principales vs juveniles)
        home_priority = self.calculate_team_priority(home_team)
        away_priority = self.calculate_team_priority(away_team)
        avg_priority = (home_priority + away_priority) / 2
        
        # Aplicar multiplicador de prioridad
        score *= (avg_priority / 10.0)
        
        # Penalty adicional para equipos claramente juveniles
        if self.is_youth_or_reserve_team(home_team) and self.is_youth_or_reserve_team(away_team):
            score *= 0.3  # Penalty severo para partidos completamente juveniles
        elif self.is_youth_or_reserve_team(home_team) or self.is_youth_or_reserve_team(away_team):
            score *= 0.5  # Penalty moderado si al menos uno es juvenil
        
        return score
    
    def find_matching_fixture(self, match_info: Dict) -> Optional[Dict]:
        """
        Encuentra el fixture que coincide con la información del partido
        Mejorado para priorizar equipos principales sobre juveniles
        """
        if not match_info or not match_info.get('date'):
            return None
        
        team1 = match_info['team1'].strip()
        team2 = match_info['team2'].strip()
        target_date = match_info['date']
        
        # Buscar fixtures en la fecha
        logger.info(f"Buscando fixtures para {target_date} con equipos {team1} vs {team2}")
        fixtures = self.search_fixtures_by_date(target_date)
        
        if not fixtures:
            logger.warning(f"No se encontraron fixtures para la fecha {target_date}")
            return None
        
        logger.info(f"Encontrados {len(fixtures)} fixtures para {target_date}")
        
        # Buscar coincidencias por nombre de equipo con scoring mejorado
        best_match = None
        best_score = 0.0
        candidates = []
        
        for fixture in fixtures:
            try:
                home_team = fixture.get('teams', {}).get('home', {}).get('name', '')
                away_team = fixture.get('teams', {}).get('away', {}).get('name', '')
                
                # Calcular score de coincidencia mejorado
                score = self.calculate_match_score(team1, team2, home_team, away_team)
                
                if score > 0:
                    is_youth = self.is_youth_or_reserve_team(home_team) or self.is_youth_or_reserve_team(away_team)
                    candidates.append({
                        'fixture': fixture,
                        'score': score,
                        'is_youth': is_youth,
                        'home_team': home_team,
                        'away_team': away_team
                    })
                    
                    logger.info(f"Candidato: {home_team} vs {away_team} (score: {score:.2f}, youth: {is_youth})")
                    
            except Exception as e:
                logger.error(f"Error procesando fixture: {e}")
                continue
        
        if not candidates:
            logger.warning(f"No se encontraron candidatos para {team1} vs {team2}")
            return None
        
        # Ordenar candidatos por score (descendente)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Seleccionar el mejor candidato
        best_candidate = candidates[0]
        
        # Log de la selección
        logger.info(f"Mejor candidato seleccionado: {best_candidate['home_team']} vs {best_candidate['away_team']}")
        logger.info(f"Score: {best_candidate['score']:.2f}, Es juvenil: {best_candidate['is_youth']}")
        
        # Si el mejor candidato es juvenil pero hay otros no juveniles con score razonable, considerar alternativas
        if best_candidate['is_youth'] and len(candidates) > 1:
            for candidate in candidates[1:3]:  # Revisar los siguientes 2 mejores
                if not candidate['is_youth'] and candidate['score'] >= best_candidate['score'] * 0.7:
                    logger.info(f"Prefiriendo equipo principal: {candidate['home_team']} vs {candidate['away_team']}")
                    logger.info(f"Score: {candidate['score']:.2f} vs {best_candidate['score']:.2f}")
                    return candidate['fixture']
        
        # Ajustar umbral según si es equipo juvenil o no
        min_threshold = 0.5 if not best_candidate['is_youth'] else 0.8
        
        if best_candidate['score'] >= min_threshold:
            logger.info(f"Fixture aceptado con score {best_candidate['score']:.2f} (umbral: {min_threshold})")
            return best_candidate['fixture']
        
        logger.warning(f"No se encontró fixture válido para {team1} vs {team2} (mejor score: {best_candidate['score']:.2f}, umbral: {min_threshold})")
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
            logger.error(f"Error extrayendo IDs de equipos: {e}")
            return None, None
    
    def process_match_text(self, match_text: str) -> Dict:
        """
        Procesa un texto de partido completo y retorna información de equipos
        """
        logger.info(f"=== PROCESANDO MATCH TEXT: {match_text} ===")
        # Parsear información del partido
        match_info = self.parse_match_text(match_text)
        
        if not match_info:
            logger.error("No se pudo parsear el texto del partido")
            return {
                'success': False,
                'error': 'No se pudo parsear el texto del partido',
                'original_text': match_text
            }
        
        # Buscar fixture correspondiente
        fixture = self.find_matching_fixture(match_info)
        
        if not fixture:
            logger.error("No se encontró fixture correspondiente")
            return {
                'success': False,
                'error': 'No se encontró fixture correspondiente',
                'match_info': match_info,
                'original_text': match_text
            }
        
        # Extraer IDs de equipos
        home_id, away_id = self.extract_team_ids(fixture)
        
        result = {
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
        logger.info(f"PROCESAMIENTO EXITOSO: {result['team_ids']['home']['name']} (ID: {home_id}) vs {result['team_ids']['away']['name']} (ID: {away_id})")
        return result

def test_fixture_matcher():
    """Función de prueba para el FixtureMatcher mejorado"""
    api_key = "d4b4999861mshc077d4879aba6d4p19f6e7jsn1bc73c757992"
    matcher = FixtureMatcher(api_key)
    
    # Casos de prueba
    test_cases = [
        "Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa",
        "Fecha: 4/5 8:00, Partido: Crystal Palace vs Brighton",
        "Fecha: 4/5 17:00, Partido: Pachuca vs América"
    ]
    
    print("=== Pruebas de FixtureMatcher MEJORADO ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Prueba {i+1} ---")
        print(f"Texto: {test_case}")
        
        result = matcher.process_match_text(test_case)
        
        if result['success']:
            team_ids = result['team_ids']
            print(f"Exito!")
            print(f"Equipo Local: {team_ids['home']['name']} (ID: {team_ids['home']['id']})")
            print(f"Equipo Visitante: {team_ids['away']['name']} (ID: {team_ids['away']['id']})")
            
            # Verificar si es juvenil
            home_youth = matcher.is_youth_or_reserve_team(team_ids['home']['name'])
            away_youth = matcher.is_youth_or_reserve_team(team_ids['away']['name'])
            print(f"¿Es juvenil? Local: {home_youth}, Visitante: {away_youth}")
        else:
            print(f"Error: {result['error']}")
        
        # Pausa entre llamadas para respetar límites de API
        time.sleep(1)

if __name__ == "__main__":
    test_fixture_matcher()