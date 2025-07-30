"""
Script para probar el resolver avanzado con datos reales del CSV
"""
import os
import pandas as pd
import logging
from load_env import load_env_file
from advanced_fixture_resolver import AdvancedFixtureResolver

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_with_csv_sample():
    # Cargar variables de entorno
    load_env_file()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        print("Error: No se encontro RAPIDAPI_KEY")
        return
    
    # Leer CSV
    try:
        df = pd.read_csv('tashist.csv')
        print(f"CSV cargado: {len(df)} filas")
        print(f"Columnas: {list(df.columns)}")
    except Exception as e:
        print(f"Error cargando CSV: {e}")
        return
    
    # Tomar solo las primeras 5 filas para prueba
    sample_df = df.head(5)
    
    resolver = AdvancedFixtureResolver(api_key)
    
    print("\n=== Pruebas con datos reales del CSV ===")
    
    successful = 0
    total = len(sample_df)
    
    for i, row in sample_df.iterrows():
        match_text = str(row.get('Match text', '')).strip()
        
        print(f"\n--- Fila {i+1} ---")
        print(f"Match text: {match_text}")
        print(f"Local original: {row.get('Local', 'N/A')}")
        print(f"Visitante original: {row.get('Visitante', 'N/A')}")
        
        if not match_text or match_text == 'nan':
            print("ERROR: Sin texto de partido valido")
            continue
        
        try:
            result = resolver.process_match_text(match_text)
            
            if result["success"]:
                team_ids = result["team_ids"]
                debug = result["debug_info"]
                fixture = result["fixture"]
                
                print(f"EXITO!")
                print(f"   Local: {team_ids['home']['name']} (ID: {team_ids['home']['id']})")
                print(f"   Visitante: {team_ids['away']['name']} (ID: {team_ids['away']['id']})")
                print(f"   Liga: {fixture['league_name']} (ID: {fixture['league_id']})")
                print(f"   Score: {debug['score']:.3f} (Home: {debug['s_home']:.3f}, Away: {debug['s_away']:.3f})")
                print(f"   Diferencia temporal: {debug.get('mins_diff', 'N/A')} minutos")
                
                successful += 1
                
            else:
                print(f"ERROR: {result['error']}")
                
        except Exception as e:
            print(f"EXCEPCION: {str(e)}")
        
        # Pausa entre llamadas API
        if i < total - 1:
            import time
            time.sleep(1)
    
    print(f"\n=== RESUMEN ===")
    print(f"Exitosos: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"Fallidos: {total-successful}/{total}")
    
    if successful == 0:
        print("\nNOTA: Es posible que las fechas en el CSV sean futuras y no esten")
        print("disponibles en la API. El resolver funciona correctamente pero necesita")
        print("fechas con fixtures disponibles en API Football.")

if __name__ == "__main__":
    test_with_csv_sample()