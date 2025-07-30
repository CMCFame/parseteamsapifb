# -*- coding: utf-8 -*-
"""
Resolver de fixtures e IDs de equipos usando API-Football v3 - VERSIÓN AVANZADA
- Entrada: fecha/hora CDMX, nombre_local, nombre_visitante (en español o abreviados)
- Salida: fixture_id, league_id, season, home_id, away_id, nombres canónicos
Basado en estrategia avanzada con tokenización y scoring inteligente
"""

import re
import math
import json
import time
import unicodedata
import requests
import logging
from datetime import datetime, timedelta, timezone
from dateutil import tz
from unidecode import unidecode

# Configurar logging
logger = logging.getLogger(__name__)

API_BASE = "https://v3.football.api-sports.io"
TIMEZONE = "America/Mexico_City"

# --- Heurísticas anti-femenil/youth ---
LEAGUE_BLOCKLIST_PAT = re.compile(
    r"(women|femenil|feminina|uwcl|u23|u21|u20|u19|u18|youth|primavera|reserves|reserve|juvenil|academia|academy)",
    re.IGNORECASE
)

# Allowlist opcional: ligas principales conocidas
LEAGUE_ALLOWLIST = set([
    39,   # Premier League
    140,  # La Liga
    61,   # Ligue 1
    78,   # Bundesliga
    135,  # Serie A
    88,   # Eredivisie
    262,  # Liga MX
    253,  # MLS
    71,   # Brasileirão
    128,  # Primera División Argentina
    94,   # Primeira Liga Portugal
    103,  # Superligaen Denmark
])

# Diccionario de alias ES->EN/OFICIAL expandido
ALIAS = {
    "man utd": "manchester united",
    "man city": "manchester city",
    "wolfsburgo": "wolfsburg",
    "américa": "america",
    "pumas": "pumas unam",
    "unión berlin": "union berlin",
    "lokomotiv": "lokomotiv moscow",
    "zenit": "zenit st. petersburg",
    "cruz azul": "cruz azul",
    "guadalajara": "guadalajara",
    "az": "az alkmaar",
    "tijuana": "club tijuana",
    "necaxa": "necaxa",
    "pachuca": "pachuca",
    "monterrey": "monterrey",
    "toluca": "toluca",
    "leon": "leon",
    "león": "leon",
    "atlas": "atlas",
    "santos": "santos laguna",
    "crystal palace": "crystal palace",
    "brighton": "brighton",
    "eagles": "crystal palace",  # águilas
    "águilas": "america",
    # Agregar más según necesidad
}

SAFE_STOPWORDS = {"cf", "fc", "ac", "bk", "if", "club", "de", "del", "la", "el", "los", "las"}

class AdvancedFixtureResolver:
    """Resolver avanzado de fixtures con tokenización y scoring inteligente"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-apisports-key": api_key,
            "Accept": "application/json"
        }
        self.cache = {}  # Cache para fixtures por fecha
    
    def _norm_name(self, s: str) -> str:
        """Normaliza nombre de equipo con alias y expansiones"""
        s = s.strip().lower()
        s = unidecode(s)  # quita acentos
        s = re.sub(r"[^a-z0-9\s\.\-]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        
        # Aplicar alias exacto
        if s in ALIAS:
            return ALIAS[s]
        
        # Expansiones básicas
        s = s.replace(" man utd", " manchester united")
        s = s.replace(" man city", " manchester city")
        s = re.sub(r"\bunión\b", "union", s)
        s = re.sub(r"\bdep\.\b", "deportivo", s)
        s = re.sub(r"\bsp\.\b", "sporting", s)
        s = re.sub(r"\bc\.\b", "club", s)
        
        return s
    
    def _tokenize(self, s: str):
        """Tokeniza nombre eliminando stopwords"""
        toks = [t for t in re.split(r"[\s\.\-]+", s) if t]
        toks = [t for t in toks if t not in SAFE_STOPWORDS and len(t) > 1]
        return toks
    
    def _token_score(self, a: str, b: str) -> float:
        """Score por tokens con bonificaciones de prefijo/substring"""
        ta, tb = set(self._tokenize(a)), set(self._tokenize(b))
        if not ta or not tb:
            return 0.0
        
        inter = len(ta & tb)
        jacc = inter / float(len(ta | tb))
        
        # Bonus por startswith exacto del primer token
        a0 = next(iter(ta)) if ta else ""
        b0 = next(iter(tb)) if tb else ""
        if a0 and b0 and (a0 == b0 or a0.startswith(b0) or b0.startswith(a0)):
            jacc += 0.2
        
        # Bonus adicional por tokens muy similares
        for token_a in ta:
            for token_b in tb:
                if len(token_a) > 3 and len(token_b) > 3:
                    if token_a in token_b or token_b in token_a:
                        jacc += 0.1
                        break
        
        return min(1.0, jacc)
    
    def _minutes_diff(self, dt1: datetime, dt2: datetime) -> int:
        """Diferencia en minutos entre dos fechas"""
        return int(abs((dt1 - dt2).total_seconds()) // 60)
    
    def _fixtures_by_date(self, date_cdmx: datetime):
        """Obtiene fixtures por fecha con cache"""
        date_str = date_cdmx.strftime("%Y-%m-%d")
        
        if date_str in self.cache:
            logger.info(f"Usando cache para fecha {date_str}")
            return self.cache[date_str]
        
        url = f"{API_BASE}/fixtures"
        params = {"date": date_str, "timezone": TIMEZONE}
        
        try:
            logger.info(f"Obteniendo fixtures para fecha {date_str}")
            r = requests.get(url, params=params, headers=self.headers, timeout=30)
            r.raise_for_status()
            data = r.json().get("response", [])
            
            self.cache[date_str] = data
            logger.info(f"Obtenidos {len(data)} fixtures para {date_str}")
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo fixtures: {e}")
            return []
    
    def _is_blocked_league(self, league_obj: dict) -> bool:
        """Verifica si la liga está en la lista negra"""
        name = league_obj.get("name") or ""
        is_blocked = bool(LEAGUE_BLOCKLIST_PAT.search(name))
        if is_blocked:
            logger.debug(f"Liga bloqueada: {name}")
        return is_blocked
    
    def _allowed_league(self, league_obj: dict) -> bool:
        """Verifica si la liga está permitida"""
        if LEAGUE_ALLOWLIST:
            is_allowed = league_obj.get("id") in LEAGUE_ALLOWLIST
            if not is_allowed:
                logger.debug(f"Liga no en allowlist: {league_obj.get('name')} (ID: {league_obj.get('id')})")
            return is_allowed
        return True  # Si no hay allowlist, se permite (pero se filtra por blocklist)
    
    def parse_match_text(self, match_text: str) -> dict:
        """Parsea el texto del partido para extraer fecha, hora y equipos"""
        logger.info(f"Parseando: {match_text}")
        
        # Patrón para extraer fecha y equipos
        pattern = r"Fecha:\s*(\d+/\d+)\s*(\d+:\d+)?,\s*Partido:\s*(.+?)\s*vs\s*(.+)"
        match = re.search(pattern, match_text)
        
        if not match:
            return {"success": False, "error": "No se pudo parsear el texto"}
        
        date_part = match.group(1)  # "4/4"
        time_part = match.group(2)  # "21:00"
        team1 = match.group(3).strip()  # "Tijuana"
        team2 = match.group(4).strip()  # "Necaxa"
        
        # Convertir fecha a datetime CDMX
        try:
            current_year = datetime.now().year
            month, day = date_part.split("/")
            
            # Si tenemos hora, usarla; si no, usar mediodía como default
            if time_part:
                hour, minute = map(int, time_part.split(":"))
            else:
                hour, minute = 12, 0
            
            # Crear datetime en timezone CDMX
            cdmx_tz = tz.gettz(TIMEZONE)
            
            # Intentar con año actual primero, luego con año anterior
            years_to_try = [current_year, current_year - 1]
            fecha_hora_cdmx = None
            
            for year in years_to_try:
                try:
                    fecha_hora_cdmx = datetime(year, int(month), int(day), hour, minute, tzinfo=cdmx_tz)
                    break
                except ValueError:
                    continue
            
            if not fecha_hora_cdmx:
                raise ValueError("No se pudo crear fecha válida")
            
            return {
                "success": True,
                "fecha_hora_cdmx": fecha_hora_cdmx,
                "local_es": team1,
                "visita_es": team2,
                "original_text": match_text
            }
            
        except Exception as e:
            logger.error(f"Error parseando fecha/hora: {e}")
            return {"success": False, "error": f"Error parseando fecha/hora: {e}"}
    
    def resolve_fixture_ids(self, fecha_hora_cdmx: datetime, local_es: str, visita_es: str, 
                           window_minutes: int = 90, use_h2h_verification: bool = False, try_previous_year: bool = True):
        """
        Resuelve fixture IDs usando estrategia avanzada
        """
        logger.info(f"Resolviendo: {local_es} vs {visita_es} en {fecha_hora_cdmx}")
        
        local_norm = self._norm_name(local_es)
        visita_norm = self._norm_name(visita_es)
        
        logger.info(f"Nombres normalizados: {local_norm} vs {visita_norm}")
        
        fixtures = self._fixtures_by_date(fecha_hora_cdmx)
        
        # Si no hay fixtures y try_previous_year es True, intentar con año anterior
        if not fixtures and try_previous_year:
            logger.info(f"No se encontraron fixtures para {fecha_hora_cdmx.year}, intentando año anterior")
            fecha_anterior = fecha_hora_cdmx.replace(year=fecha_hora_cdmx.year - 1)
            fixtures = self._fixtures_by_date(fecha_anterior)
            
            if fixtures:
                logger.info(f"Encontrados fixtures en año anterior: {fecha_anterior.year}")
                # Actualizar la fecha de referencia
                fecha_hora_cdmx = fecha_anterior
        
        if not fixtures:
            return {"status": "not_found", "reason": "no_fixtures_for_date"}
        
        # Filtro de ventana temporal y ligas permitidas
        candidates = []
        for fx in fixtures:
            try:
                # Parsear fecha del fixture
                fx_date_str = fx["fixture"]["date"]
                if fx_date_str.endswith("Z"):
                    fx_date_str = fx_date_str[:-1] + "+00:00"
                
                fx_dt_utc = datetime.fromisoformat(fx_date_str)
                fx_dt_cdmx = fx_dt_utc.astimezone(tz.gettz(TIMEZONE))
                
                mins = self._minutes_diff(fx_dt_cdmx, fecha_hora_cdmx)
                
                # Verificar ventana temporal y liga
                if mins <= window_minutes and fx.get("league"):
                    if not self._allowed_league(fx["league"]):
                        continue
                    if self._is_blocked_league(fx["league"]):
                        continue
                    
                    home = fx["teams"]["home"]["name"]
                    away = fx["teams"]["away"]["name"]
                    home_norm = self._norm_name(home)
                    away_norm = self._norm_name(away)
                    
                    s_home = self._token_score(local_norm, home_norm)
                    s_away = self._token_score(visita_norm, away_norm)
                    
                    # Score combinado con penalty por diferencia temporal
                    score = 0.7 * s_home + 0.7 * s_away - 0.01 * mins
                    
                    # Bonificación si ambos lados muy altos
                    if s_home >= 0.85 and s_away >= 0.85:
                        score += 0.2
                    
                    # Bonificación por liga principal conocida
                    if fx["league"]["id"] in LEAGUE_ALLOWLIST:
                        score += 0.05
                    
                    candidates.append({
                        "score": score,
                        "mins_diff": mins,
                        "fixture": fx,
                        "home_norm": home_norm,
                        "away_norm": away_norm,
                        "s_home": s_home,
                        "s_away": s_away
                    })
                    
                    logger.debug(f"Candidato: {home} vs {away} (score: {score:.3f}, mins: {mins})")
                    
            except Exception as e:
                logger.error(f"Error procesando fixture: {e}")
                continue
        
        if not candidates:
            return {"status": "not_found", "reason": "no_candidates_in_window"}
        
        # Ordenar por score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        best = candidates[0]
        
        logger.info(f"Mejor candidato: score={best['score']:.3f}, mins_diff={best['mins_diff']}")
        
        # Verificación H2H opcional (deshabilitada por defecto para evitar muchas llamadas API)
        if use_h2h_verification and len(candidates) > 1:
            # Verificar si hay empate cerrado
            tie = [c for c in candidates if abs(c["score"] - best["score"]) <= 0.05]
            if len(tie) > 1:
                logger.info("Empate detectado, usando verificación H2H")
                best = self._break_tie_with_h2h(tie, fecha_hora_cdmx)
        
        fx = best["fixture"]
        result = {
            "status": "ok",
            "fixture_id": fx["fixture"]["id"],
            "kickoff_cdmx": fx["fixture"]["date"],
            "league_id": fx["league"]["id"],
            "league_name": fx["league"]["name"],
            "season": fx["league"]["season"],
            "home_id": fx["teams"]["home"]["id"],
            "home_name": fx["teams"]["home"]["name"],
            "away_id": fx["teams"]["away"]["id"],
            "away_name": fx["teams"]["away"]["name"],
            "score_debug": {
                "score": round(best["score"], 4),
                "mins_diff": best["mins_diff"],
                "s_home": round(best["s_home"], 3),
                "s_away": round(best["s_away"], 3),
                "local_norm": local_norm,
                "visita_norm": visita_norm,
            }
        }
        
        logger.info(f"Resultado: {result['home_name']} vs {result['away_name']} (ID: {result['fixture_id']})")
        return result
    
    def _break_tie_with_h2h(self, candidates, fecha_hora_cdmx: datetime):
        """Rompe empates usando head-to-head verification"""
        target_date = fecha_hora_cdmx.date()
        
        for c in candidates:
            fx = c["fixture"]
            home_id = fx["teams"]["home"]["id"]
            away_id = fx["teams"]["away"]["id"]
            
            url = f"{API_BASE}/fixtures/headtohead"
            params = {"h2h": f"{home_id}-{away_id}"}
            
            try:
                r = requests.get(url, params=params, headers=self.headers, timeout=30)
                if r.status_code != 200:
                    continue
                    
                for item in r.json().get("response", []):
                    item_date_str = item["fixture"]["date"]
                    if item_date_str.endswith("Z"):
                        item_date_str = item_date_str[:-1] + "+00:00"
                    
                    dt_utc = datetime.fromisoformat(item_date_str)
                    dt_cdmx = dt_utc.astimezone(tz.gettz(TIMEZONE))
                    
                    if dt_cdmx.date() == target_date:
                        logger.info(f"H2H verification exitosa para {fx['teams']['home']['name']} vs {fx['teams']['away']['name']}")
                        return c
                        
            except Exception as e:
                logger.error(f"Error en H2H verification: {e}")
                continue
        
        # Si no hubo coincidencia exacta por fecha, quedarse con el mejor score
        return candidates[0]
    
    def process_match_text(self, match_text: str) -> dict:
        """Procesa un texto de partido completo y retorna información de equipos"""
        # Parsear información del partido
        parse_result = self.parse_match_text(match_text)
        
        if not parse_result["success"]:
            return {
                "success": False,
                "error": parse_result["error"],
                "original_text": match_text
            }
        
        # Resolver fixture
        resolve_result = self.resolve_fixture_ids(
            parse_result["fecha_hora_cdmx"],
            parse_result["local_es"],
            parse_result["visita_es"]
        )
        
        if resolve_result["status"] != "ok":
            return {
                "success": False,
                "error": f"No se encontró fixture: {resolve_result.get('reason', 'unknown')}",
                "original_text": match_text,
                "parse_info": parse_result
            }
        
        # Formatear resultado final
        return {
            "success": True,
            "match_info": {
                "date": parse_result["fecha_hora_cdmx"].strftime("%Y-%m-%d"),
                "time": parse_result["fecha_hora_cdmx"].strftime("%H:%M"),
                "team1": parse_result["local_es"],
                "team2": parse_result["visita_es"]
            },
            "fixture": {
                "id": resolve_result["fixture_id"],
                "league_id": resolve_result["league_id"],
                "league_name": resolve_result["league_name"],
                "season": resolve_result["season"]
            },
            "team_ids": {
                "home": {
                    "id": resolve_result["home_id"],
                    "name": resolve_result["home_name"],
                    "original_name": parse_result["local_es"]
                },
                "away": {
                    "id": resolve_result["away_id"],
                    "name": resolve_result["away_name"],
                    "original_name": parse_result["visita_es"]
                }
            },
            "original_text": match_text,
            "debug_info": resolve_result["score_debug"]
        }

def test_advanced_resolver():
    """Función de prueba para el resolver avanzado"""
    import os
    from load_env import load_env_file
    
    # Cargar variables de entorno
    load_env_file()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        print("Error: No se encontró RAPIDAPI_KEY")
        return
    
    resolver = AdvancedFixtureResolver(api_key)
    
    # Casos de prueba
    test_cases = [
        "Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa",
        "Fecha: 4/5 8:00, Partido: Crystal Palace vs Brighton",
        "Fecha: 4/5 17:00, Partido: Pachuca vs América",
        "Fecha: 4/5 21:10, Partido: Cruz Azul vs Pumas"
    ]
    
    print("=== Pruebas de Resolver Avanzado ===")
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Prueba {i+1} ---")
        print(f"Texto: {test_case}")
        
        result = resolver.process_match_text(test_case)
        
        if result["success"]:
            team_ids = result["team_ids"]
            debug = result["debug_info"]
            print(f"✅ Éxito!")
            print(f"   Local: {team_ids['home']['name']} (ID: {team_ids['home']['id']})")
            print(f"   Visitante: {team_ids['away']['name']} (ID: {team_ids['away']['id']})")
            print(f"   Liga: {result['fixture']['league_name']}")
            print(f"   Score: {debug['score']} (Home: {debug['s_home']}, Away: {debug['s_away']})")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Pausa entre llamadas
        time.sleep(1)

if __name__ == "__main__":
    test_advanced_resolver()