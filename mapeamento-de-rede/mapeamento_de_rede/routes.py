import os
from flask import Blueprint, render_template

# Resolve paths to module-level templates/static directories (absolute paths)
pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
template_folder = os.path.join(pkg_dir, 'templates')
static_folder = os.path.join(pkg_dir, 'static')

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
