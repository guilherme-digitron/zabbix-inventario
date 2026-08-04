from flask import Flask

from database.database import db


from api.zabbix import list_items

items = list_items("Guilherme")

for item in items:
    print(item["name"])
    print(item["key_"])
    print(item["lastvalue"])
    print("-" * 40)

"""
app = Flask(__name__)

app.config.from_pyfile("config.py")

db.init_app(app)

with app.app_context():
    db.create_all()

from routes.dashboard import dashboard

from routes.hosts import hosts

app.register_blueprint(dashboard)

app.register_blueprint(hosts)

app.run(host="0.0.0.0",port=5000)
"""
