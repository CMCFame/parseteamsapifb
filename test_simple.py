"""
Script de prueba simplificado para validar mejoras
"""

import pandas as pd
import requests
import sys
import os

# Agregar el directorio actual al path para importar app
sys.path.append(os.getcwd())

try:
    from app import TeamAssociationSystem, extraer_equipos_del_excel, extraer_contexto_partidos
    print("Modulos importados correctamente")
except ImportError as e:
    print(f"Error importando modulos: {e}")
    sys.exit(1)

def test_context_extraction():
    """Prueba extraccion de contexto del CSV"""
    print("\n--- Probando extraccion de contexto ---")
    
    try:
        df = pd.read_csv('tashist.csv')
        print(f"Archivo cargado: {len(df)} filas")
        
        # Extraer equipos y contexto
        teams_list = extraer_equipos_del_excel(df)
        team_context = extraer_contexto_partidos(df)
        
        print(f"Equipos unicos: {len(teams_list)}")
        print(f"Equipos con contexto: {len(team_context)}")
        
        # Mostrar algunos ejemplos
        print("\nEjemplos de contexto:")
        count = 0
        for team, matches in team_context.items():
            if count >= 3:
                break
            print(f"\n{team} ({len(matches)} partidos):")
            for match in matches[:2]:
                print(f"  vs {match['opponent']} - {match.get('fecha', 'N/A')}")
            count += 1
            
        return teams_list, team_context
        
    except Exception as e:
        print(f"Error: {e}")
        return [], {}

def test_api_connection():
    """Prueba conexion con API"""
    print("\n--- Probando conexion API ---")
    
    api_key = "d4b4999861mshc077d4879aba6d4p19f6e7jsn1bc73c757992"
    
    headers = {
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': api_key
    }
    
    url = "https://v3.football.api-sports.io/teams"
    params = {'league': 262, 'season': 2024}  # Liga MX
    
    try:
        print("Conectando a API Football...")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            teams = data.get('response', [])
            print(f"Exito! Equipos obtenidos: {len(teams)}")
            
            # Mostrar algunos equipos
            if teams:
                print("\nEjemplos de equipos Liga MX:")
                for i, item in enumerate(teams[:5]):
                    team = item.get('team', {})
                    print(f"  {team.get('name')} (ID: {team.get('id')})")
            
            # Convertir a formato usado por la app
            api_teams = []
            for item in teams:
                team = item.get('team', {})
                api_teams.append({
                    'id': team.get('id'),
                    'name': team.get('name'),
                    'code': team.get('code'),
                    'country': team.get('country'),
                    'logo': team.get('logo')
                })
            
            return True, api_teams
        else:
            print(f"Error API: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"Error conexion: {e}")
        return False, []

def test_matching():
    """Prueba el matching mejorado"""
    print("\n--- Probando matching mejorado ---")
    
    # Datos de ejemplo para probar
    sample_teams = [
        {"id": 541, "name": "América", "code": "AME", "country": "Mexico"},
        {"id": 1032, "name": "Cruz Azul", "code": "CRU", "country": "Mexico"},
        {"id": 1054, "name": "Pachuca", "code": "PAC", "country": "Mexico"},
        {"id": 1046, "name": "Monterrey", "code": "MTY", "country": "Mexico"},
    ]
    
    association_system = TeamAssociationSystem()
    
    # Caso de prueba con contexto
    team_name = "América"
    context = [
        {"opponent": "Pachuca", "match_text": "Fecha: 4/5 17:00, Partido: Pachuca vs América"},
        {"opponent": "Cruz Azul", "match_text": "Fecha: 4/10 19:00, Partido: América vs Cruz Azul"}
    ]
    
    # Sin contexto
    match_without = association_system.find_best_match(team_name, sample_teams)
    
    # Con contexto
    match_with = association_system.find_best_match(team_name, sample_teams, context)
    
    print(f"\nEquipo: {team_name}")
    
    if match_without:
        print(f"Sin contexto: {match_without['api_team']['name']} "
              f"(Confianza: {match_without['confidence']:.2f})")
    
    if match_with:
        boost = match_with.get('context_boost', 0)
        print(f"Con contexto: {match_with['api_team']['name']} "
              f"(Confianza: {match_with['confidence']:.2f}, Boost: +{boost:.2f})")

if __name__ == "__main__":
    print("=== Pruebas de mejoras ===")
    
    # Prueba 1: Extraccion de contexto
    teams_list, team_context = test_context_extraction()
    
    # Prueba 2: Conexion API
    api_connected, api_teams = test_api_connection()
    
    # Prueba 3: Matching
    test_matching()
    
    print("\n=== Pruebas completadas ===")