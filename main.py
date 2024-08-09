from microdot import Microdot, Response, redirect, send_file
from microdot_utemplate import render_template
import network
import json
import machine, os, gc

app = Microdot()
Response.default_content_type = 'text/html'
lista_apps = []

#Cargar las apps desde el dir apps
def load_apps():
    for app_item in os.listdir("apps"):
        if app_item == "__init__.py" or app_item == "__pycache__":
            pass
        else:
            lista_apps.append(app_item.replace('.py', ''))
            
    return lista_apps

#funcion que importa los modulos instalados
def import_modules(path):
    with open(f'apps/{path}.py') as f:
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
    f = open('config.json', 'r')
    config = json.load(f)
    f.close()
    return render_template('home.html',
                            titulo="KIOSK HOME",
                            modo=config["wifi"]["modo"],
                            apps=lista_apps)

@app.route('/sobre')
def sobre(request):
    return render_template('sobre.html', appname="SOBRE", titulo="SOBRE")

@app.route('/static/<path:path>')
def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    return send_file('static/' + path)

@app.route('/static/icons/<path:path>')
def icons(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
        
    return send_file('static/icons/' + path)

@app.route('/appsm', methods=["GET", "POST"])
def app_manager(request):
    if request.method == "POST":
        pass
    
    return render_template('appmanager.html')

@app.route('/reiniciar', methods=["POST"])
def desconect(request):
    if request.method == "POST":
        machine.reset()
        return redirect('/')
        
@app.route('/wifi', methods=["GET", "POST"])
def wifi_conect(request):
    redes = []
            
    context = {"name":None,
                   "msj":None,
                   "ssid":None,
                   "password":None,
                   "modo":"ap",
                   "ip":"",
                   "appname":"CONECTAR A RED"}
        
    config = None
        
    try:
        config = open("config.json")
        config = json.load(config)
            
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
            f = open("config.json", "w")
            json.dump(config, f)
            f.close()
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
                            ip=context["ip"])

if __name__ == '__main__':
    app = install_apps(app)
    app.run(port=80, debug=True)