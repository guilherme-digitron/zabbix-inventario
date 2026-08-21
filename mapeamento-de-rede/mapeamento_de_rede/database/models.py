# esquema SQLite simples
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    mac TEXT,
    hostname TEXT,
    vendor TEXT,
    device_type TEXT,
    os TEXT,
    last_seen TIMESTAMP,
    raw JSON
);
CREATE TABLE IF NOT EXISTS connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_ip TEXT,
    target_ip TEXT,
    confidence TEXT,
    method TEXT,
    detected_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    summary TEXT
);
"""
