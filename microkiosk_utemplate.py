from utemplate import recompile
from microdot import Microdot, send_file
import os
import gc

# Caché de loaders
_loaders = {
    'main': None,  # Loader para templates principales
    'apps': {}     # Diccionario de loaders por app
}
# Cache de templates base
base_templates_cache = {}
# In your microdot_utemplate.py
def load_base_templates():
    base_templates = ['head', 'footer', 'top_bar']
    for tpl in base_templates:
        try:
            with open(f'templates/{tpl}.html', 'r') as f:
                base_templates_cache[tpl] = f.read()
            print(f"{tpl}.html guardado en cache")
            print(base_templates_cache[tpl])
        except Exception as e:
            print(f"Error cargando template base {tpl}: {e}")
            base_templates_cache[tpl] = f"<!-- Error cargando {tpl} -->"
            
    return base_templates_cache

def init_templates(main_template_dir='templates', loader_class=recompile.Loader):
    """Inicializa el sistema de templates para el directorio principal y apps"""
    global _loaders
    _loaders['main'] = loader_class(None, main_template_dir)

def init_app_templates(app_name, app_template_dir=None):
    """Registra los templates de una app específica"""
    if app_template_dir is None:
        app_template_dir = f"apps/{app_name}/templates"
    
    _loaders['apps'][app_name] = recompile.Loader(None, app_template_dir)

def render_template(template, *args, **kwargs):
    """Renderiza un template del directorio principal"""
    if _loaders['main'] is None:
        init_templates()
    
    try:
        gc.collect()
        return _loaders['main'].load(template)(*args, **kwargs)
    except Exception as e:
        print(f"Error renderizando {template}: {str(e)}")
        return f"<h1>Error en template {template}</h1>"

def render_app_template(app_name, template, *args, **kwargs):
    """Renderiza un template de una app específica"""
    if app_name not in _loaders['apps']:
        init_app_templates(app_name)
    
    try:
        gc.collect()
        return _loaders['apps'][app_name].load(template)(*args, **kwargs)
    
    except Exception as e:
        print(f"Error en app {app_name}, template {template}: {str(e)}")
        return f"<h1>Error en template {template}</h1>"
    