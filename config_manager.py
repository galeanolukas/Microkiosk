import ujson
import uos

CONFIG_FILE = "config.json"

def read_config():
    """Leer el archivo de configuración actual."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return ujson.load(f)
    except:
        # Si el archivo no existe o está corrupto, retorna configuración por defecto
        return {"wifi": {"modo": "ap", "ssid": "Microkiosk", "getway": "192.168.1.1", "ip": "", "password": "Microkiosk"},
                         "favoritos": {},
                         "apps": ["home_app", "test_app"],
                         "config": {"debug": "True", "port": 80, "theme": "light"}
                }

def write_config(new_config):
    """Escribir nuevas configuraciones en el archivo."""
    try:
        with open(CONFIG_FILE, "w") as f:
            ujson.dump(new_config, f)
        return True
    except Exception as e:
        print(f"Error al escribir config: {e}")
        return False

def update_config(pkey, key, value):
    """Actualizar una configuración específica."""
    config = read_config()
    if peky:
        config[pkey][key] = value  # Modifica solo la clave especificada
    else:
        config[key] = value
        
    return write_config(config)