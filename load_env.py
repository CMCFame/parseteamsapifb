"""
Cargador de variables de entorno desde archivo .env
"""
import os

def load_env_file(env_file='.env'):
    """Carga variables de entorno desde un archivo .env"""
    if not os.path.exists(env_file):
        print(f"Archivo {env_file} no encontrado")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    print(f"Variable de entorno cargada: {key.strip()}")
    
    return True

if __name__ == "__main__":
    load_env_file()