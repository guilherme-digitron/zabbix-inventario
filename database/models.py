from database.database import db
from datetime import datetime

class HostOverride(db.Model):
    __tablename__ = "host_overrides"
    id = db.Column(db.Integer, primary_key=True)
    zabbix_hostid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    hostname = db.Column(db.String(256))
    ip = db.Column(db.String(64))
    mac = db.Column(db.String(64))
    username = db.Column(db.String(128))
    anydesk = db.Column(db.String(128))
    inventory = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
