from flask import Blueprint, render_template, current_app

rede_bp = Blueprint(
    "rede",
    __name__,
    template_folder="../../mapeamento-de-rede/templates",
    static_folder="../../mapeamento-de-rede/static",
)

@rede_bp.route("/rede")
def rede_page():
    # Página principal do mapeamento de rede
    return render_template("rede.html")
