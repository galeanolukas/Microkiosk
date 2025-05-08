# author: galeano lucas
# version: 1.0
# name: Terminal MicroPython
# info: Consola de Micropython
from microdot import Microdot, Response, send_file
from microkiosk_utemplate import render_app_template
import gc

terminal = Microdot()

class TerminalBuffer:
    def __init__(self, max_lines=30):
        self.max_lines = max_lines
        self.lines = []
        
    def add_output(self, text):
        """Añade texto al buffer"""
        lines = text.splitlines()
        for line in lines:
            if line.strip():  # Ignorar líneas vacías
                if len(self.lines) >= self.max_lines:
                    self.lines.pop(0)
                self.lines.append(line)
        gc.collect()
    
    def get_output(self, last_n=20):
        """Obtiene las últimas líneas"""
        return '\n'.join(self.lines[-last_n:])

terminal_buffer = TerminalBuffer()

def execute_command(command):
    """Ejecuta un comando y captura el output manualmente"""
    result = None
    error = None
    
    try:
        # Intenta evaluar primero (para expresiones)
        try:
            result = eval(command, globals(), {})
        except SyntaxError:
            # Si falla eval, probamos con exec
            exec(command, globals(), {})
            
    except Exception as e:
        error = f"Error: {type(e).__name__}: {str(e)[:100]}"
    
    return result, error

@terminal.route('/')
def index(request):
    return render_app_template('terminal', 'index.html', titulo="Terminal MicroPython")

@terminal.route('/static/<path:path>')
def serve_static(request, path):
    return send_file(f"apps/terminal/static/{path}")

@terminal.route('/exec', methods=['POST'])
def exec_command(request):
    """Ejecuta comandos con captura manual de output"""
    command = request.body.decode('utf-8')[:128]
    
    # Registrar el comando
    terminal_buffer.add_output(f">>> {command}")
    
    # Ejecutar el comando
    result, error = execute_command(command)
    
    if error:
        terminal_buffer.add_output(error)
        return {'status': 'error', 'output': terminal_buffer.get_output(), 'error': error}
    
    if result is not None:
        terminal_buffer.add_output(str(result))
    
    gc.collect()
    return {'status': 'success', 'output': terminal_buffer.get_output()}

@terminal.route('/output')
def get_output(request):
    """Obtiene el output actual"""
    return {'output': terminal_buffer.get_output()}