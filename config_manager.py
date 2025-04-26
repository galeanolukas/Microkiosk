import json
import os
CONFIG_FILE = "config.json"

def init_config():
    default_config = {
        "wifi": {
            "modo": "ap",
            "ssid": "Microkiosk",
            "password": "Microkiosk",
            "gateway": "",
            "dns": "",
            "ip": "",
            "subnet": "",
            "ip_fija": "False"
        },
        "bt": {
            "active": "False",
            "name": "Microkiosk_BT",
            "mode": "peripheral"
        },
        "favoritos": {},
        "apps": ["home_app", "test_app"],
        "config": {
            "debug": "True",
            "port": 80,
            "theme": "light"
        }
    }

    # Si no existe, crear config con valores por defecto
    if CONFIG_FILE not in os.listdir():
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f)
        return

    # Si existe, cargar y completar claves faltantes
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    except:
        config = {}

    # Completar claves principales y subclaves
    for key, default_value in default_config.items():
        if key not in config:
            config[key] = default_value
        elif isinstance(default_value, dict):
            for subkey, subvalue in default_value.items():
                config[key].setdefault(subkey, subvalue)

    # Guardar el archivo actualizado
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def read_config():
    """Leer el archivo de configuración actual."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        # Si el archivo no existe o está corrupto, retorna configuración por defecto
        return {"wifi": {"modo": "ap", "ssid": "Microkiosk", "password": "Microkiosk", "gateway": "", "dns": "", "ip": "", "subnet": "", "ip_fija": "True"},
                         "favoritos": {},
                         "apps": ["home_app", "test_app"],
                         "config": {"debug": "False", "port": 80, "theme": "light"},
                         "hostname": "",
                }

def write_config(new_config):
    """Escribir nuevas configuraciones en el archivo."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_config, f)
        return True
    except Exception as e:
        print(f"Error al escribir config: {e}")
        return False

def update_config(pkey, key, value):
    """Actualizar una configuración específica."""
    config = read_config()
    if pkey:
        config[pkey][key] = value  # Modifica solo la clave especificada
    else:
        config[key] = value
        
    return write_config(config)