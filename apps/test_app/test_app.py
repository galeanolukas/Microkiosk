from microdot import Microdot, Response
from microdot_utemplate import render_template
test_app = Microdot()

@test_app.route('/')
def test(request, methods=["GET"]):
    return render_template('test_app/index.html', mensaje="Hola Mundo!!", titulo="TESTAPP")
