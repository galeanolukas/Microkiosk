import json
import os, gc
import tarfile
import config_manager
from microdot_utemplate import init_app_templates, init_static_routes

def exists(path):
    """Reemplazo de os.path.exists para MicroPython."""
    try:
        os.stat(path)
        return True
    except OSError:
        return False

def join(*args):
    """Reemplazo de os.path.join para MicroPython."""
    return '/'.join(args)

def find_file(directory, extensions):
    """Busca el primer archivo que coincida con una extensión dada."""
    if not exists(directory):
        return None
    
    for file in os.listdir(directory):
        if any(file.endswith(ext) for ext in extensions):
            return join(directory, file)
    return None

#Busca y comprueba la existencia archivos en los directorios x tipo
def find_file(directory, extensions):
    """Busca el primer archivo que coincida con una extensión dada."""
    if not exists(directory):
        return None
    for file in os.listdir(directory):
        if any(file.endswith(ext) for ext in extensions):
            return join(directory, file)
    return None

# Busca la info en la metadata de la app
def parse_app_metadata(app_dir):
    metadata = {}
    try:
        with open(f'{app_dir}', 'r') as f:
            for line in f:
                if line.startswith("# "):
                    key_value = line[2:].split(":", 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        metadata[key.lower()] = value
                else:
                    break  # termina cuando encuentra la primera línea que no es comentario
    except Exception as e:
        return False
        print(f"Error leyendo metadata en {app_dir}: {e}")
    return metadata

# Cargar/Actualiza las apps desde el dir apps
def load_apps():
    excepciones = ["__init__.py", "__pycache__", ".DS_Store", "README.md"]
    apps_info = {}
    config_json = config_manager.read_config()
    config_apps = config_json.get("apps", {})
    
    # Obtener lista de apps en directorio
    dir_apps = [d for d in os.listdir('apps') 
               if d not in excepciones 
               and (os.stat(join('apps', d))[0] & 0x4000)]  # Paréntesis corregido aquí

    # Verificar apps eliminadas
    for app_name in list(config_apps.keys()):
        if app_name not in dir_apps:
            print(f"App eliminada: {app_name}")
            del config_apps[app_name]

    # Procesar apps existentes/nuevas
    for app_dir in dir_apps:
        app_path = join('apps', app_dir)
        script_file = join(app_path, f'{app_dir}.py')
        
        # Verificar si es una app válida (tiene archivo principal)
        if not exists(script_file):
            continue
            
        # Obtener metadatos
        metadata = parse_app_metadata(script_file)
        app_config = config_apps.get(app_dir, {})
        
        # Rutas de recursos
        static_path = join(app_path, 'static')
        templates_path = join(app_path, 'templates')
        
        # Buscar archivos de recursos
        icon_file = find_file(static_path, ['.png', '.jpg', '.jpeg', '.svg', '.webp']) if exists(static_path) else None
        style_file = find_file(static_path, ['.css']) if exists(static_path) else None
        template_file = find_file(templates_path, ['.html']) if exists(templates_path) else None
        
        # Determinar si es una app nueva o modificada
        is_new_app = app_dir not in config_apps
        is_modified = False
        
        if not is_new_app:
            # Verificar si los archivos principales han cambiado
            old_mtime = app_config.get('_mtime', 0)
            current_mtime = os.stat(script_file)[8]  # st_mtime
            is_modified = current_mtime > old_mtime
        
        # Actualizar información de la app
        apps_info[app_dir] = {
            "name": metadata.get("name", app_dir),
            "url": f"/{app_dir}/",
            "icon": f"/{app_dir}/static/{icon_file}" if icon_file else "/static/micropython.png",
            "style": f"/{app_dir}/static/{style_file}" if style_file else None,
            "template": template_file if template_file else None,
            "author": metadata.get("author", ""),
            "info": metadata.get("info", ""),
            "version": metadata.get("version", ""),
            "fav": app_config.get("fav", False),
            "_mtime": os.stat(script_file)[8],  # Guardar timestamp de modificación
            "_new": is_new_app,
            "_modified": is_modified
        }
        
        if is_new_app:
            print(f"Nueva app detectada: {app_dir}")
        elif is_modified:
            print(f"App actualizada: {app_dir}")

    # Actualizar configuración solo si hay cambios
    if apps_info != config_json.get("apps", {}):
        config_manager.update_config(None, "apps", apps_info)
        print("Configuración de apps actualizada")
    
    return apps_info

def import_module_from_file(module_name, filepath):
    """Importar un módulo a mano en MicroPython."""
    try:
        # Crea un espacio de nombres limpio
        module_globals = {}
        with open(filepath) as f:
            exec(f.read(), module_globals)
            
        return module_globals
    except Exception as e:
        print(f"Error importando {module_name}: {e}")
        return None

def copy_common_files(app_name):
    """Copia archivos comunes desde los directorios principales a la app solo si no existen"""
    common_files = {
        'templates': ['head.html', 'top_bar.html', 'footer.html'],
        'static': ['w3.css', 'default_icons.css', 'default_theme.css'],
    }
    
    for subdir, files in common_files.items():
        # Primero verificar/crear el directorio destino
        dst_dir = 'apps/{}/{}'.format(app_name, subdir)
        try:
            os.stat(dst_dir)
        except OSError:
            try:
                os.mkdir(dst_dir)
                print("[INFO] Directorio creado:", dst_dir)
            except OSError as e:
                print("[ERROR] No se pudo crear directorio {}: {}".format(dst_dir, e))
                continue  # Saltar esta subdir si no podemos crear el directorio
        
        for file in files:
            src = '{}/{}'.format(subdir, file)
            dst = '{}/{}'.format(dst_dir, file)
            
            # Verificar si el archivo ya existe en destino
            try:
                os.stat(dst)
                print("[INFO] Archivo ya existe en destino:", dst)
                continue  # Saltar este archivo
            except OSError:
                pass  # El archivo no existe, proceder a copiar
            
            # Verificar si el archivo fuente existe
            try:
                os.stat(src)
            except OSError:
                print("[WARN] Archivo fuente no encontrado:", src)
                continue
            
            # Copiar el archivo
            try:
                with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                    while True:
                        chunk = fsrc.read(256)  # Leer en bloques pequeños
                        if not chunk:
                            break
                        fdst.write(chunk)
                print("[INFO] Copiado {} → {}".format(src, dst))
            except Exception as e:
                print("[ERROR] Fallo al copiar {}: {}".format(src, e))

def install_apps(current_app):
    apps = load_apps()

    for app_name in apps:
        try:
            gc.collect()  # 1. Limpieza de memoria antes de cargar cada app
            app_path = f"apps/{app_name}/{app_name}.py"
            module = import_module_from_file(app_name, app_path)

            if module and app_name in module:
                sub_app = module[app_name]
                # 2. Inicializar templates de la app
                init_app_templates(app_name)
                # 3. Copiar archivos comunes necesarios
                copy_common_files(app_name)
                current_app.mount(sub_app, url_prefix=f'/{app_name}')
                print(f"✔️ App {app_name} instalada correctamente")
            else:
                print(f"⚠️ App {app_name} no define '{app_name}' correctamente")

        except Exception as e:
            print(f"❌ Error instalando {app_name}: {e}")

    return current_app

def verificar_estructura_app(app_folder):
    """Verifica que la app tenga la estructura correcta."""
    # Ruta base de la app
    base_path = f"apps/{app_folder}"

    # Verificar existencia de la carpeta base
    if not exists(base_path):
        return False, "No existe la carpeta de la aplicación."

    # Verificar existencia del archivo principal
    if not find_file(base_path, [".py"]):
        return False, f"Falta el archivo principal {app_folder}.py."

    # Verificar carpetas templates/ y static/
    templates_path = f"{base_path}/templates"
    static_path = f"{base_path}/static"

    if not exists(templates_path):
        return False, "Falta la carpeta templates/"
    
    if not exists(static_path):
        return False, "Falta la carpeta static/"

    return True, "Estructura correcta."
