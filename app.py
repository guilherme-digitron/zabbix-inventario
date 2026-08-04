from flask import Flask

from database.database import db

# inicialização normal da aplicação
app = Flask(__name__)
app.config.from_pyfile("config.py")
# garante secret key para flash
app.secret_key = app.config.get('SECRET_KEY', 'dev')

# importa models para que create_all crie as tabelas
import database.models

db.init_app(app)

with app.app_context():
    # cria tabelas (HostOverride)
    db.create_all()

from routes.dashboard import dashboard
from routes.hosts import hosts

app.register_blueprint(dashboard)
app.register_blueprint(hosts)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
