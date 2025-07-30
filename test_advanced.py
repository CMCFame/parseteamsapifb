"""
Script de prueba para el resolver avanzado sin emojis
"""
import os
import time
import logging
from load_env import load_env_file
from advanced_fixture_resolver import AdvancedFixtureResolver

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_advanced_resolver():
    # Cargar variables de entorno
    load_env_file()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        print("Error: No se encontro RAPIDAPI_KEY")
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
    
    successful = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- Prueba {i+1} ---")
        print(f"Texto: {test_case}")
        
        try:
            result = resolver.process_match_text(test_case)
            
            if result["success"]:
                team_ids = result["team_ids"]
                debug = result["debug_info"]
                fixture = result["fixture"]
                
                print(f"EXITO!")
                print(f"   Local: {team_ids['home']['name']} (ID: {team_ids['home']['id']})")
                print(f"   Visitante: {team_ids['away']['name']} (ID: {team_ids['away']['id']})")
                print(f"   Liga: {fixture['league_name']} (ID: {fixture['league_id']})")
                print(f"   Score: {debug['score']} (Home: {debug['s_home']}, Away: {debug['s_away']})")
                print(f"   Diferencia temporal: {debug['mins_diff']} minutos")
                
                successful += 1
                
                # Verificar si es equipo juvenil
                home_name = team_ids['home']['name'].lower()
                away_name = team_ids['away']['name'].lower()
                
                is_youth = any(indicator in home_name + " " + away_name 
                             for indicator in ['u23', 'u21', 'u20', 'youth', 'reserve', 'ii'])
                
                if is_youth:
                    print(f"   ADVERTENCIA: Posible equipo juvenil detectado")
                else:
                    print(f"   OK: Equipos principales")
                    
            else:
                print(f"ERROR: {result['error']}")
                
        except Exception as e:
            print(f"EXCEPCION: {str(e)}")
        
        # Pausa entre llamadas
        if i < total - 1:
            time.sleep(1)
    
    print(f"\n=== RESUMEN ===")
    print(f"Exitosos: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"Fallidos: {total-successful}/{total}")

if __name__ == "__main__":
    test_advanced_resolver()