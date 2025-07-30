"""
Script para probar diferentes fechas y encontrar fixtures disponibles
"""
import os
import time
import requests
from datetime import datetime, timedelta
from load_env import load_env_file

def test_date_ranges():
    load_env_file()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        print("Error: No se encontro RAPIDAPI_KEY")
        return
    
    headers = {
        "x-apisports-key": api_key,
        "Accept": "application/json"
    }
    
    # Probar fechas recientes (últimos 30 días)
    today = datetime.now()
    
    print("Probando fechas recientes para encontrar fixtures...")
    
    dates_to_try = []
    for i in range(1, 31):  # Últimos 30 días
        date = today - timedelta(days=i)
        dates_to_try.append(date)
    
    found_dates = []
    
    for date in dates_to_try[:10]:  # Solo probar 10 fechas para no gastar API calls
        date_str = date.strftime("%Y-%m-%d")
        
        url = "https://v3.football.api-sports.io/fixtures"
        params = {"date": date_str}
        
        try:
            print(f"Probando fecha: {date_str}")
            r = requests.get(url, params=params, headers=headers, timeout=30)
            
            if r.status_code == 200:
                data = r.json().get("response", [])
                if data:
                    found_dates.append((date_str, len(data)))
                    print(f"  ✓ {len(data)} fixtures encontrados")
                    
                    # Mostrar algunos equipos de ejemplo
                    for fixture in data[:3]:
                        home = fixture["teams"]["home"]["name"]
                        away = fixture["teams"]["away"]["name"]
                        league = fixture["league"]["name"]
                        print(f"    - {home} vs {away} ({league})")
                else:
                    print(f"  ✗ Sin fixtures")
            else:
                print(f"  ✗ Error API: {r.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        time.sleep(1)  # Pausa para respetar límites
    
    print(f"\n=== RESUMEN ===")
    print(f"Fechas con fixtures encontradas: {len(found_dates)}")
    for date_str, count in found_dates:
        print(f"  {date_str}: {count} fixtures")
    
    if found_dates:
        print(f"\nPuedes usar fechas como: {found_dates[0][0]} para probar el resolver")

if __name__ == "__main__":
    test_date_ranges()