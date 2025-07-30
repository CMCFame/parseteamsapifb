"""
Script de prueba para validar las mejoras en el matching de equipos
usando información contextual del archivo tashist.csv
"""

import pandas as pd
import json
import requests
from app import TeamAssociationSystem, extraer_equipos_del_excel, extraer_contexto_partidos

def test_with_sample_data():
    """Prueba con datos de muestra"""
    print("Probando con datos de muestra...")
    
    # Cargar datos de muestra
    sample_teams = [
        {"id": 541, "name": "América", "code": "AME", "country": "Mexico"},
        {"id": 1032, "name": "Cruz Azul", "code": "CRU", "country": "Mexico"},
        {"id": 1040, "name": "Pumas UNAM", "code": "PUM", "country": "Mexico"},
        {"id": 1044, "name": "Tigres UNAM", "code": "TIG", "country": "Mexico"},
        {"id": 1046, "name": "Monterrey", "code": "MTY", "country": "Mexico"},
        {"id": 1050, "name": "Guadalajara", "code": "GDL", "country": "Mexico"},
        {"id": 1054, "name": "Pachuca", "code": "PAC", "country": "Mexico"},
        {"id": 1058, "name": "Necaxa", "code": "NEC", "country": "Mexico"},
        {"id": 50, "name": "Manchester City", "code": "MCI", "country": "England"},
        {"id": 33, "name": "Manchester United", "code": "MUN", "country": "England"},
        {"id": 49, "name": "Chelsea", "code": "CHE", "country": "England"},
        {"id": 40, "name": "Liverpool", "code": "LIV", "country": "England"},
    ]
    
    # Crear sistema de asociación
    association_system = TeamAssociationSystem()
    
    # Casos de prueba
    test_cases = [
        {
            "team": "América", 
            "context": [
                {"opponent": "Pachuca", "match_text": "Fecha: 4/5 17:00, Partido: Pachuca vs América"},
                {"opponent": "Cruz Azul", "match_text": "Fecha: 4/10 19:00, Partido: América vs Cruz Azul"}
            ]
        },
        {
            "team": "Man City", 
            "context": [
                {"opponent": "Man Utd", "match_text": "Fecha: 4/6 9:30, Partido: Man Utd vs Man City"},
                {"opponent": "Chelsea", "match_text": "Fecha: 4/10 15:00, Partido: Man City vs Chelsea"}
            ]
        },
        {
            "team": "Tijuana", 
            "context": [
                {"opponent": "Necaxa", "match_text": "Fecha: 4/4 21:00, Partido: Tijuana vs Necaxa"},
            ]
        }
    ]
    
    print("\\n📊 Resultados de prueba:")
    print("-" * 60)
    
    for test_case in test_cases:
        team_name = test_case["team"]
        context = test_case["context"]
        
        # Prueba sin contexto
        match_without_context = association_system.find_best_match(team_name, sample_teams)
        
        # Prueba con contexto
        match_with_context = association_system.find_best_match(team_name, sample_teams, context)
        
        print(f"\\n🏆 Equipo: {team_name}")
        
        if match_without_context:
            print(f"   Sin contexto: {match_without_context['api_team']['name']} "
                  f"(Confianza: {match_without_context['confidence']:.2f})")
        else:
            print("   Sin contexto: No encontrado")
            
        if match_with_context:
            context_boost = match_with_context.get('context_boost', 0)
            print(f"   Con contexto: {match_with_context['api_team']['name']} "
                  f"(Confianza: {match_with_context['confidence']:.2f}, "
                  f"Boost: +{context_boost:.2f})")
        else:
            print("   Con contexto: No encontrado")

def test_with_tashist_csv():
    """Prueba con el archivo tashist.csv real"""
    print("\\n🎯 Probando con tashist.csv...")
    
    try:
        # Cargar archivo
        df = pd.read_csv('tashist.csv')
        print(f"✅ Archivo cargado: {len(df)} filas")
        
        # Extraer equipos y contexto
        teams_list = extraer_equipos_del_excel(df)
        team_context = extraer_contexto_partidos(df)
        
        print(f"📊 Equipos únicos encontrados: {len(teams_list)}")
        print(f"🎯 Equipos con contexto: {len(team_context)}")
        
        # Mostrar algunos ejemplos
        print("\\n🔍 Ejemplos de contexto extraído:")
        print("-" * 40)
        
        count = 0
        for team, matches in team_context.items():
            if count >= 5:  # Solo mostrar 5 ejemplos
                break
            print(f"\\n{team} ({len(matches)} partidos):")
            for match in matches[:2]:  # Solo 2 partidos por equipo
                print(f"  • vs {match['opponent']} - {match['match_text']}")
            count += 1
            
        return teams_list, team_context
        
    except FileNotFoundError:
        print("❌ Archivo tashist.csv no encontrado")
        return [], {}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return [], {}

def test_api_connection(api_key):
    """Prueba conexión con API Football"""
    print("\\n🌐 Probando conexión con API Football...")
    
    headers = {
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': api_key
    }
    
    # Probar con Liga MX (ID: 262)
    url = "https://v3.football.api-sports.io/teams"
    params = {'league': 262, 'season': 2024}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            teams = data.get('response', [])
            print(f"✅ API conectada exitosamente")
            print(f"📊 Equipos Liga MX obtenidos: {len(teams)}")
            
            # Mostrar algunos ejemplos
            if teams:
                print("\\n🏆 Ejemplos de equipos de Liga MX:")
                for i, item in enumerate(teams[:5]):
                    team = item.get('team', {})
                    print(f"  • {team.get('name')} (ID: {team.get('id')})")
            
            return True, teams
        else:
            print(f"❌ Error de API: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False, []
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: La API tardó demasiado en responder")
        return False, []
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False, []

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de mejoras en matching de equipos")
    print("=" * 60)
    
    # Prueba 1: Datos de muestra
    test_with_sample_data()
    
    # Prueba 2: Archivo tashist.csv
    teams_list, team_context = test_with_tashist_csv()
    
    # Prueba 3: API Football (usando tu API key)
    api_key = "d4b4999861mshc077d4879aba6d4p19f6e7jsn1bc73c757992"
    api_connected, api_teams = test_api_connection(api_key)
    
    # Prueba integrada si todo está disponible
    if teams_list and team_context and api_connected and api_teams:
        print("\\n🎉 Ejecutando prueba integrada...")
        print("-" * 40)
        
        association_system = TeamAssociationSystem()
        
        # Probar con algunos equipos que sabemos que están en Liga MX
        test_teams = ["América", "Cruz Azul", "Pachuca", "Monterrey", "Tijuana"]
        
        for team_name in test_teams:
            if team_name in team_context:
                context = team_context[team_name]
                match = association_system.find_best_match(team_name, api_teams, context)
                
                if match:
                    boost = match.get('context_boost', 0)
                    print(f"✅ {team_name} → {match['api_team']['name']} "
                          f"(ID: {match['api_team']['id']}, "
                          f"Confianza: {match['confidence']:.2f}, "
                          f"Boost: +{boost:.2f})")
                else:
                    print(f"❌ {team_name} → No encontrado")
    
    print("\\n🏁 Pruebas completadas!")