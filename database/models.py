from database.database import db

class Computer(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    hostid = db.Column(db.String(30), unique=True)

    hostname = db.Column(db.String(100))

    usuario = db.Column(db.String(100))

    departamento = db.Column(db.String(100))

    patrimonio = db.Column(db.String(50))

    observacao = db.Column(db.Text)
