from microdot import Microdot, Response
from microkiosk_utemplate import render_app_template
test_app = Microdot()

@test_app.route('/')
def test(request, methods=["GET"]):
    return render_app_template('test_app', 'index.html', request, mensaje="Hola Mundo!!", titulo="TESTAPP")
