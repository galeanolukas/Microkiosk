from microdot import Microdot, Response, redirect, send_file
from microdot_utemplate import render_template
# from microdot_static import Static
import bluetooth
import network
import json
import machine, os, gc, sys

app = Microdot()
Response.default_content_type = 'text/html'
# app.mount('/static', Static('./static'))

# Inicializa Bluetooth
#ble = bluetooth.BLE()
#ble.active(True)

lista_apps = []

def scan_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()  # Devuelve una lista de tuplas con la información de las redes
    wifi_list = []
    for net in networks:
        wifi_list.append(net[0].decode('utf-8'))
        
    return wifi_list

# funcion que carga la configuracion
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except OSError:
        return {}
    
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)


#Cargar las apps desde el dir apps
def load_apps():
    config = load_config()
    for app_dir in os.listdir("apps"):
        if app_dir == "__init__.py" or app_dir == "__pycache__":
            pass
        else:
            lista_apps.append(app_dir)
            
    config["apps"] = lista_apps
    save_config(config)

    return lista_apps

#funcion que importa los modulos instalados
def import_modules(path):
    with open(f'apps/{path}/{path}.py') as f:
        code = f.read()
        exec(code)
        
#instala los modulos dentro de la app principal
def install_apps(current_app):
    lista = load_apps()
    if lista:
        for app_name in lista:
            import_modules(app_name)
            if app_name in dir():
                sub_app = eval(app_name)
                current_app.mount(sub_app, url_prefix=f'/{app_name}')
            
    return current_app
                               
@app.route('/')
def home(request):
    config = load_config()
    board = sys.platform
    return render_template('home.html',
                            titulo="MICROKIOSK",
                            modo=config["wifi"]["modo"],
                            apps=lista_apps,
                            board=board.upper())

@app.route('/sobre')
def sobre(request):
    config = load_config()
    return render_template('sobre.html', appname="SOBRE", titulo="SOBRE", modo=config["wifi"]["modo"])

@app.route('/static/<path:path>')
def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    
    return send_file('static/' + path)
# 
# @app.route('/static/icons/<path:path>')
# def serve_svg(request, path):
#     file_path = os.path.join("static/icons/", path)
#     print(file_path)
#     if os.path.exists(file_path):
#         with open(file_path, 'rb') as f:
#             content = f.read()
#         return Response(content, content_type='image/svg+xml')
#     else:
#         return 'File not found', 404

@app.route('/appm', methods=["GET", "POST"])
def app_manager(request):
    config = load_config()
    if request.method == "POST":
        pass
    
    return render_template('appmanager.html',
                           titulo="APPMANAGER",
                           appname="APPS MANAGER",
                           modo=config["wifi"]["modo"],
                           apps=config["apps"])

@app.route('/reiniciar', methods=["POST"])
def desconect(request):
    if request.method == "POST":
        machine.reset()
        return redirect('/')

@app.route('/bt', methods=["GET", "POST"])
def blue(request):
    config = load_config()
    
    if request.nethod == "POST":
        pass
        
    return render_template('bt.html',
                           bt=config["bt"]["active"],
                           modo=config["wifi"]["modo"],
                           appname="BLUETOOTH MANAGER", titulo="")
        
@app.route('/wifi', methods=["GET", "POST"])
def wifi_conect(request):
    redes = scan_wifi()
    
    context = {"name":None,
                   "msj":None,
                   "ssid":None,
                   "password":None,
                   "modo":"ap",
                   "ip":"",
                   "appname":"WIFI MANAGER"}
        
    config = None
        
    try:
        config = load_config()
            
    except OSError:
        pass
            
    if request.method == "POST":
        ssid = request.form['essid']
        psk = request.form['password']
        modo = request.form['modo']
        ip = request.form['ip']
        if ssid and psk:
            config["wifi"]["ssid"] = ssid
            config["wifi"]["password"] = psk
            config["wifi"]["modo"] = modo
            config["wifi"]["ip"] = ip
            save_config(config)
            machine.reset()
            return redirect('/')
        else:
            context['msj'] = "Debe completar los campos!"
            return redirect('/')

    if config:
        context["ssid"] = config["wifi"]["ssid"]
        context["password"] = config["wifi"]["password"]
        context["modo"] = config["wifi"]["modo"]
    else:
        pass
                
    return render_template('wifi.html', ssid=context["ssid"],
                            titulo="WIFI CONECTAR",
                            msj=context["msj"],
                            appname=context["appname"],
                            modo=context["modo"],
                            password=context["password"],
                            redes=redes,
                            ip=context["ip"])

if __name__ == '__main__':
    app = install_apps(app)
    app.run(port=80, debug=True)