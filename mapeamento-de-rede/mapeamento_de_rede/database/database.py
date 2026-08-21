import sqlite3
import threading
import time
import json
from .models import CREATE_SQL

class Database:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, path):
        self.path = path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    @classmethod
    def get(cls, path="mapeamento-de-rede/data/network.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = Database(path)
            return cls._instance

    def _ensure_schema(self):
        cur = self._conn.cursor()
        cur.executescript(CREATE_SQL)
        self._conn.commit()

    def upsert_device(self, device):
        cur = self._conn.cursor()
        # simples upsert por ip
        cur.execute("SELECT id FROM devices WHERE ip = ?", (device.get("ip"),))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE devices SET mac=?, hostname=?, vendor=?, device_type=?, os=?, last_seen=?, raw=? WHERE id=?",
                        (device.get("mac"), device.get("hostname"), device.get("vendor"), device.get("device_type"), device.get("os"), device.get("last_seen"), json.dumps(device), row["id"]))
            did = row["id"]
        else:
            cur.execute("INSERT INTO devices (ip,mac,hostname,vendor,device_type,os,last_seen,raw) VALUES (?,?,?,?,?,?,?,?)",
                        (device.get("ip"), device.get("mac"), device.get("hostname"), device.get("vendor"), device.get("device_type"), device.get("os"), device.get("last_seen"), json.dumps(device)))
            did = cur.lastrowid
        self._conn.commit()
        return did

    def insert_connection(self, conn):
        cur = self._conn.cursor()
        cur.execute("INSERT INTO connections (source_ip,target_ip,confidence,method,detected_at) VALUES (?,?,?,?,?)",
                    (conn.get("source"), conn.get("target"), conn.get("confidence"), conn.get("method"), conn.get("detected_at")))
        self._conn.commit()

    def list_devices(self):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM devices ORDER BY last_seen DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def list_topology(self):
        cur = self._conn.cursor()
        cur.execute("SELECT source_ip,target_ip,confidence,method,detected_at FROM connections")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
