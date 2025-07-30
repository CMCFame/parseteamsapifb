"""
Script de prueba completo del nuevo sistema fixture-based
"""

import pandas as pd
from fixture_matcher import FixtureMatcher
import json

def test_full_process():
    """Prueba el proceso completo con tashist.csv"""
    print("=== Prueba del Proceso Completo Fixture-Based ===")
    
    # Cargar archivo CSV
    try:
        df = pd.read_csv('tashist.csv')
        print(f"Archivo cargado: {len(df)} filas")
    except Exception as e:
        print(f"Error cargando archivo: {e}")
        return
    
    # Verificar columnas
    if 'Match text' not in df.columns:
        print("Error: No se encontró la columna 'Match text'")
        print("Columnas disponibles:", list(df.columns))
        return
    
    # Inicializar FixtureMatcher
    api_key = "d4b4999861mshc077d4879aba6d4p19f6e7jsn1bc73c757992"
    matcher = FixtureMatcher(api_key)
    
    # Procesar una muestra pequeña
    sample_size = 5
    sample_df = df.head(sample_size)
    
    print(f"\nProcesando muestra de {sample_size} partidos...")
    print("-" * 60)
    
    results = []
    successful = 0
    failed = 0
    
    for i, row in sample_df.iterrows():
        match_text = str(row.get('Match text', '')).strip()
        
        print(f"\nProcesando fila {i+1}: {match_text}")
        
        if not match_text or match_text == 'nan':
            print("  Error: Sin texto de partido")
            failed += 1
            continue
        
        try:
            result = matcher.process_match_text(match_text)
            
            if result['success']:
                team_ids = result['team_ids']
                print(f"  Exito!")
                print(f"    Local: {team_ids['home']['name']} (ID: {team_ids['home']['id']})")
                print(f"    Visitante: {team_ids['away']['name']} (ID: {team_ids['away']['id']})")
                print(f"    Fecha: {result['match_info']['date']}")
                successful += 1
            else:
                print(f"  Error: {result['error']}")
                failed += 1
            
            results.append({
                'fila': i+1,
                'texto_original': match_text,
                'resultado': result
            })
            
        except Exception as e:
            print(f"  Error procesando: {e}")
            failed += 1
    
    # Resumen
    print(f"\n=== RESUMEN ===")
    print(f"Total procesado: {len(results)}")
    print(f"Exitosos: {successful}")
    print(f"Fallidos: {failed}")
    print(f"Tasa de exito: {(successful/len(results)*100):.1f}%" if results else "0%")
    
    # Crear DataFrame con resultados para Excel
    if results:
        print(f"\nCreando datos para Excel...")
        
        excel_data = []
        for item in results:
            row_data = sample_df.iloc[item['fila']-1].to_dict()
            result = item['resultado']
            
            if result['success']:
                team_ids = result['team_ids']
                row_data['Local_API_ID'] = team_ids['home']['id']
                row_data['Local_API_Name'] = team_ids['home']['name']
                row_data['Visitante_API_ID'] = team_ids['away']['id']
                row_data['Visitante_API_Name'] = team_ids['away']['name']
                row_data['Status'] = 'FOUND'
            else:
                row_data['Local_API_ID'] = None
                row_data['Local_API_Name'] = 'NOT_FOUND'
                row_data['Visitante_API_ID'] = None
                row_data['Visitante_API_Name'] = 'NOT_FOUND'
                row_data['Status'] = 'NOT_FOUND'
                row_data['Error'] = result.get('error', '')
            
            excel_data.append(row_data)
        
        # Guardar en Excel
        result_df = pd.DataFrame(excel_data)
        output_file = 'test_results_fixture_based.xlsx'
        result_df.to_excel(output_file, index=False)
        print(f"Resultados guardados en: {output_file}")
        
        # Mostrar DataFrame
        print(f"\nDatos generados:")
        print(result_df[['Local', 'Visitante', 'Local_API_ID', 'Visitante_API_ID', 'Status']].to_string())

if __name__ == "__main__":
    test_full_process()