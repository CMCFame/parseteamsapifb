"""
Script simple para probar fechas disponibles
"""
import os
import time
import requests
from datetime import datetime, timedelta
from load_env import load_env_file

def test_simple_dates():
    load_env_file()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    headers = {
        "x-apisports-key": api_key,
        "Accept": "application/json"
    }
    
    # Probar algunas fechas específicas conocidas
    test_dates = [
        "2024-12-15",  # Fecha reciente
        "2024-12-01", 
        "2024-11-30",
        "2024-11-23",
        "2024-11-16",
    ]
    
    print("Probando fechas especificas...")
    
    for date_str in test_dates:
        url = "https://v3.football.api-sports.io/fixtures"
        params = {"date": date_str}
        
        try:
            print(f"\nFecha: {date_str}")
            r = requests.get(url, params=params, headers=headers, timeout=30)
            
            if r.status_code == 200:
                data = r.json().get("response", [])
                print(f"  Fixtures: {len(data)}")
                
                if data:
                    # Filtrar algunas ligas principales
                    main_leagues = []
                    for fixture in data:
                        league_name = fixture["league"]["name"]
                        league_id = fixture["league"]["id"]
                        
                        # Ligas principales conocidas
                        if league_id in [39, 140, 78, 135, 61, 262, 253]:
                            home = fixture["teams"]["home"]["name"]
                            away = fixture["teams"]["away"]["name"]
                            main_leagues.append(f"    {home} vs {away} ({league_name})")
                    
                    if main_leagues:
                        print("  Partidos de ligas principales:")
                        for match in main_leagues[:5]:
                            print(match)
                    else:
                        print("  Sin partidos de ligas principales, mostrando algunos:")
                        for fixture in data[:3]:
                            home = fixture["teams"]["home"]["name"]
                            away = fixture["teams"]["away"]["name"]
                            league = fixture["league"]["name"]
                            print(f"    {home} vs {away} ({league})")
                    
                    if len(data) > 0:
                        print(f"  --> Esta fecha tiene datos! Puedes usarla para probar")
                        break
            else:
                print(f"  Error API: {r.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_simple_dates()