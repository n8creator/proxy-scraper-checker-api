from __future__ import annotations

from collections import defaultdict
from sqlite3 import Connection

from fastapi import APIRouter, Depends

from api.database import get_db_connection

router = APIRouter()


def get_db():
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()


@router.get("/proxies")
def get_proxies(db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM proxies")
    proxies = cursor.fetchall()
    return {"count": len(proxies), "proxies": [dict(proxy) for proxy in proxies]}


@router.get("/proxies/{protocol}")
def get_proxies_by_protocol(protocol: str, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM proxies WHERE protocol = ?", (protocol,))
    proxies = cursor.fetchall()
    return {"count": len(proxies), "proxies": [dict(proxy) for proxy in proxies]}


@router.get("/stats")
def get_statistics(db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT protocol, continent_name, country_name
        FROM proxies
        WHERE protocol IN ('http', 'socks4', 'socks5')
    """)

    stats = defaultdict(lambda: {"total_count": 0, "by_continents": defaultdict(int), "by_country": defaultdict(int)})

    for row in cursor.fetchall():
        protocol, continent, country = row
        stats[protocol]["total_count"] += 1
        stats[protocol]["by_continents"][continent] += 1
        stats[protocol]["by_country"][country] += 1

    # Convert defaultdict to regular dict for JSON serialization
    return {
        proto: {
            "total_count": data["total_count"],
            "by_continents": dict(sorted(data["by_continents"].items(), key=lambda x: x[1], reverse=True)),
            "by_country": dict(sorted(data["by_country"].items(), key=lambda x: x[1], reverse=True)),
        }
        for proto, data in stats.items()
    }
