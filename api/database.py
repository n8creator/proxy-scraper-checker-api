from __future__ import annotations

import sqlite3
from pathlib import Path


def get_db_connection():
    db_path = Path(__file__).parent.parent / "out" / "proxies.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
