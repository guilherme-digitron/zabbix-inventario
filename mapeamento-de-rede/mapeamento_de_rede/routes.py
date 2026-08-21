import os
from flask import Blueprint, render_template

# Resolve paths to module-level templates/static directories (absolute paths)
# __file__ is .../mapeamento_de_rede/routes.py; we want the module root at mapeamento-de-rede (two levels up)
module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
template_folder = os.path.join(module_root, 'templates')
static_folder = os.path.join(module_root, 'static')

# Expose static files under /mapeamento-de-rede/static
rede_bp = Blueprint(
    "rede",
    __name__,
    template_folder=template_folder,
    static_folder=static_folder,
    static_url_path='/mapeamento-de-rede/static'
)

@rede_bp.route("/rede")
def rede_page():
    # Página principal do mapeamento de rede
    return render_template("rede.html")
