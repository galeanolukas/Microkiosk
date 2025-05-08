from microdot import Microdot, Response, redirect, send_file
from tinydb import TinyDB, Query
import bt_manager
import network
import json, errno
import machine, os, gc, sys, re
import tarfile
from config_manager import read_config, update_config
from apps_manager import install_apps
from microkiosk_utemplate import render_template
import socket
import micropython

app = Microdot()
#Response.default_content_type = 'text/html'
db = TinyDB('users.json')
users = db.table('users')
User = Query()
# Crear usuario admin por defecto si no existe
if not users.contains(User.username == 'admin'):
    users.insert({'username': 'admin', 'password': 'admin'})
# Cargar Configuracion guardada
config = read_config()

@app.route('/system_info')
def system_info(request):
    uname = os.uname()
    return {
        "system": {
            "name": uname.sysname,
            "hostname": uname.nodename,
            "firmware_version": uname.version,
            "hardware": uname.machine
        }
    }

@app.route('/mem_stats')
def mem_stats():
    # Obtener estadísticas de memoria
    gc.collect()  # Liberar memoria no usada antes de medir
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    mem_total = mem_free + mem_alloc
    ram_usage_percent = (mem_alloc / mem_total) * 100
    # Obtener información de Flash (si está disponible)
    try:
        flash_total = 16 * 1024 * 1024  # 16 MB (ajusta según tu micro)
        flash_used = os.statvfs('/')[1] * os.statvfs('/')[3]  # Bloque usado * tamaño bloque
        flash_free = flash_total - flash_used
        flash_usage_percent = (flash_used / flash_total) * 100
    except:
        flash_free, flash_total, flash_usage_percent = "N/A", "N/A", "N/A"
        
    return {"ram_percent": round(ram_usage_percent),
            "flash_percent": round(flash_usage_percent),
            "ram_free": round(mem_free),
            "flash_free": round(flash_free),
            "ram_total": round(mem_total),
            "flash_total": round(flash_total / 1024 * 1024)}

#Decorador para sessiones
def login_required(view_func):
    async def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user'):  # Verifica si ya está autenticado
            return redirect('/login')
        return await view_func(request, *args, **kwargs)
    return wrapper

def scan_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    return [net[0].decode('utf-8') for net in wlan.scan()]

@app.route('/bt/scan', methods=["POST"])
def scan_devices(request):
    config = read_config()
    bt_device = bt_manager.iniciar(config["bt"])
    bt_manager.escanear(bt_device, 3000)
    return redirect("/bt")

@app.route('/config/save-css', methods=['POST'])
def save_css(request):
    css_type = request.args.get('type')  # 'theme' o 'icons'
    if css_type not in ['theme', 'icons']:
        return 'Tipo inválido', 400
    
    try:
        # Sobrescribe el archivo correspondiente
        with open(f'static/default_{css_type}.css', 'w') as f:
            f.write(request.body.decode())
        return 'CSS actualizado', 200
    except Exception as e:
        return f'Error: {str(e)}', 500

def temas_disponibles():
    temas = []
    try:
        with open('static/default_theme.css', 'r') as f:
            contenido = f.read()
            
            # Dividir por "body." y luego extraer el nombre
            partes = contenido.split('body.')
            for parte in partes[1:]:  # Ignorar la primera parte
                if '-theme {' in parte:
                    tema = parte.split('-theme {')[0]
                    if tema not in temas:
                        temas.append(tema)
    
    except Exception as e:
        print("Error leyendo temas:", e)
    return temas

#### Vistas por defecto del SO ###
@app.route('/login', methods=['GET', 'POST'])
def login(request):
    error = None
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        user = users.get((User.username == username) & (User.password == password))
        
        if user:
            response = redirect('/home')
            response.set_cookie('user', username)
            return response
        
        else:
            error = 'Usuario o contraseña incorrectos'
            
    return render_template('login.html', error=error,
                           appname="LOGIN",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"])
    
@app.route('/')
def home(request):
    sys_info = system_info(request)["system"]
    memoria = mem_stats()
    lista_apps = config.get("apps", None)
    return render_template('home.html',
                            titulo="MICROKIOSK",
                            modo=config["wifi"]["modo"],
                            tema=config["config"]["theme"],
                            appname="HOME",
                            apps=lista_apps,
                            mem=memoria,
                            user=User.username,
                            sys_info=sys_info
                           )

@app.route('/sobre')
def sobre(request):
    return render_template('sobre.html',
                           appname="SOBRE",
                           titulo="SOBRE",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"])

def get_content_type(filename):
    if filename.endswith('.css'):
        return 'text/css'
    elif filename.endswith('.svg'):
        return 'image/svg+xml'
    elif filename.endswith('.js'):
        return 'application/javascript'
    elif filename.endswith('.png'):
        return 'image/png'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return 'image/jpg'
    return 'application/octet-stream'

# ===== [Servidor de archivos estáticos] =====
@app.route('/static/<path:path>')
@app.route('/apps/<app_name>/static/<path:path>')
def serve_static(request, path, app_name=None):
    # Determinar directorio base
    base_dir = f'apps/{app_name}/static' if app_name else 'static'
    file_path = f'{base_dir}/{path}'

    try:
        return send_file(file_path, content_type=get_content_type(path))
    except OSError:
        # Intentar fallback global si es una app
        if app_name:
            try:
                return send_file(f'static/{path}', content_type=get_content_type(path))
            except OSError:
                pass
        return "Not found", 404

@app.route('/appm', methods=["GET", "POST"])
def app_manager(request):
    config = read_config()
    if request.method == "POST":
        uploaded_file = request.files.get('file')
        if uploaded_file:
            filename = uploaded_file.filename
            app_name = None
            # Guardar el archivo temporalmente
            temp_path = "/tmp/" + filename
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            # Detectar tipo de archivo
            if filename.endswith(".tar"):
                with tarfile.open(temp_path, "r:r") as tar:
                    tar.extractall("apps/")
                    app_name = tar.getnames()[0].split('/')[0]
            else:
                return render_template('appmanager.html',
                                       appname="APPS MANAGER",
                                       modo=config["wifi"]["modo"],
                                       apps=config["apps"],
                                       msj="Archivo no soportado. Solo .tar",
                                       tema=config["config"]["theme"])

            # Eliminar archivo temporal
            try:
                os.remove(temp_path)
            except:
                pass
            # Verificar estructura antes de registrar
            ok, mensaje = verificar_estructura_app(app_name)
            if not ok:
                # Borrar carpeta si está incompleta
                import shutil
                shutil.rmtree(f"apps/{app_name}")
                return render_template('global', 'appmanager.html',
                                       appname="APPS MANAGER",
                                       modo=config["wifi"]["modo"],
                                       apps=config["apps"],
                                       msj=f"Error en la app: {mensaje}",
                                       tema=config["config"]["theme"])

            # Registrar y montar app
            if app_name and app_name not in config["apps"]:
                config["apps"].append(app_name)
                update_config(None, "apps", config["apps"])

                global lista_apps
                lista_apps = config["apps"]
                install_apps(app)

            return redirect('/appm')

    return render_template('appmanager.html',
                           appname="APPS MANAGER",
                           modo=config["wifi"]["modo"],
                           apps=config["apps"],
                           msj=None,
                           tema=config["config"]["theme"]
                           )

def show_message(title, message, message_type='info', 
                details=None, action=None, new_ip=None,
                redirect_url='/', button_text='Aceptar'):
    # Mapear tipos de mensaje a clases W3.CSS
    type_classes = {
        'info': ('w3-blue', 'w3-blue'),
        'success': ('w3-green', 'w3-green'),
        'warning': ('w3-orange', 'w3-orange'),
        'error': ('w3-red', 'w3-red'),
        'reconnect': ('w3-indigo', 'w3-indigo')
    }
    
    message_class, button_class = type_classes.get(
        message_type, ('w3-blue', 'w3-blue'))
    
    return render_template('message.html',
        title=title,
        message=message,
        details=details,
        message_class=message_class,
        button_class=button_class,
        action=action,
        new_ip=new_ip,
        redirect_url=redirect_url,
        button_text=button_text
    )

@app.route('/reiniciar', methods=["GET", "POST"])
def reiniciar(request):
    if request.method == "POST":
        import time
        time.sleep(1)
        machine.reset()
        return redirect('/')
    
    return render_template('reboot.html',
                           appname="APAGAR PLACA",
                           titulo="",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"])

@app.route('/bt', methods=["GET", "POST"])
def blue(request):
    config = read_config()
    devices = None
    
    if request.method == "POST":
        bt_status = request.form.get("bt_status")
        bt_name = request.form.get("bt_name") or "Microkiosk_BT"
        bt_mode = request.form.get("bt_mode") or "peripheral"

        config["bt"]["active"] = "True" if bt_status == "on" else "False"
        config["bt"]["name"] = bt_name
        config["bt"]["mode"] = bt_mode

        update_config(None, "bt", config["bt"])
    #Inicia el dispositivo si esta habilitado
    bt_device = bt_manager.iniciar(config["bt"])
    
    return render_template('bt.html',
                           bt=config["bt"]["active"],
                           bt_name=config["bt"].get("name", "Microkiosk_BT"),
                           bt_mode=config["bt"].get("mode", "peripheral"),
                           modo=config["wifi"]["modo"],
                           appname="BLUETOOTH MANAGER",
                           devices=bt_manager.devices_found,
                           titulo="CONFIGURACIÓN BLUETOOTH",
                           tema=config["config"]["theme"])

@app.route('/wifi', methods=["GET", "POST"])
def wifi_conect(request):
    redes = scan_wifi()
    config = read_config()
    config_wifi = {"wifi": {}}
    
    context = {
        "name": None,
        "msj": None,
        "ssid": None,
        "password": None,
        "modo": "ap",
        "ip": "",
        "appname": "WIFI MANAGER",
        "tema": config["config"]["theme"]
    }
    # Cargar datos actuales de la config
    if config:
        context["ssid"] = config["wifi"]["ssid"]
        context["password"] = config["wifi"]["password"]
        context["modo"] = config["wifi"]["modo"]
        if eval(config["wifi"]["ip_fija"]):
            context["ip"] = config["wifi"]["ip"]
    # Si es GET y hay un ssid seleccionado desde el navegador
    if request.method == "GET":
        ssid = request.args.get('n')
        
        if ssid:
            context["ssid"] = ssid
            context["password"] = ""  # limpiar password al seleccionar otra red
            context["modo"] = "st"     # cambia automáticamente a modo estación

    if request.method == "POST":
        ssid = request.form['essid']
        psk = request.form['password']
        modo = request.form['modo']
        ip = request.form['ip']

        if ssid and psk:
            update_config("wifi", "ssid", ssid)
            update_config("wifi", "password", psk)
            update_config("wifi", "modo", modo)
            update_config("wifi", "ip", ip)
            new_ip = read_config().get("wifi")["ip"]
            
            return show_message(request, title="Configuración Actualizada",
                                message="La configuración de red ha sido modificada.",
                                message_type='reconnect',
                                action='reconnect',
                                new_ip=new_ip,
                                redirect_url=f'http://{new_ip}',
                                button_text='Conectar Ahora')
        else:
            context['msj'] = "Debe completar SSID y contraseña."
            return redirect('/wifi')

    return render_template('wifi.html', redes=redes, **context)

@app.route('/logout')
def logout(request):
    response = redirect('/login')
    response.delete_cookie('user')
    return response

@app.route('/config', methods=['GET', 'POST'])
def config_view(request):
    config = read_config()

    if request.method == 'POST':
        if request.form.get('debug') == 'on':
            new_debug = "True"
        else:
            new_debug = "False"
            
        new_port = int(request.form.get('port'))
        new_theme = request.form.get('theme')
        # Comprobamos si hay cambios que requieren reinicio
        requiere_reinicio = (
            config['config']['debug'] != new_debug or
            config['config']['port'] != new_port
        )

        update_config("config", "debug", new_debug)
        update_config("config", "port", new_port)
        update_config("config", "theme", new_theme)

        if requiere_reinicio:
            return render_template('restarting.html',
                                   appname="CONFIGURACION",
                                   modo=config["wifi"]["modo"],
                                   tema=config["config"]["theme"])

        return redirect('/config')

    return render_template('config.html',
                           port=config['config']['port'],
                           theme=config["config"]["theme"],
                           debug=config['config']['debug'],
                           appname="CONFIGURACION",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"],
                           temas=temas_disponibles())

def run_stable_server():
    while True:
        try:
            print("Iniciando servidor...")
            #Ejecuta el servidor del framework
            app.run(port=config["config"]["port"],
                    debug=eval(config["config"]["debug"]))
        except OSError as e:
            if e.errno == errno.ENOTCONN:
                print("Reiniciando por error de conexión...")
                continue
            else:
                print(f"Error crítico: {str(e)}")
                break
        except KeyboardInterrupt:
            print("Servidor detenido manualmente")
            break
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            continue

if __name__ == '__main__':
    #Carga la config del Sistema
    config = read_config()
    #Instala las apps cargadas
    app = install_apps(app)
    run_stable_server()