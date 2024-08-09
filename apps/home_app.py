from microdot import Microdot, Response
home_app = Microdot()

@home_app.route('/')
def prueba(request, methods=["GET"]):
    return "App Hola Mundo!!!"

@home_app.route('/prueba')
def test(request, methods=["GET"]):
    return "Hola Mundo Prueba!!!"