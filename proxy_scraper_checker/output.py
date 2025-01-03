from __future__ import annotations

import json
import logging
import os
import stat
from shutil import rmtree
from typing import TYPE_CHECKING

import maxminddb
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from proxy_scraper_checker import fs, sort
from proxy_scraper_checker.db_models import Base, ProxyDB
from proxy_scraper_checker.geodb import GEODB_PATH
from proxy_scraper_checker.null_context import NullContext
from proxy_scraper_checker.utils import IS_DOCKER

if TYPE_CHECKING:
    from collections.abc import Sequence

    from proxy_scraper_checker.proxy import Proxy
    from proxy_scraper_checker.settings import Settings
    from proxy_scraper_checker.storage import ProxyStorage

_logger = logging.getLogger(__name__)


def _create_proxy_list_str(*, anonymous_only: bool, include_protocol: bool, proxies: Sequence[Proxy]) -> str:
    return "\n".join(
        proxy.as_str(include_protocol=include_protocol)
        for proxy in proxies
        if not anonymous_only or (proxy.exit_ip is not None and proxy.host != proxy.exit_ip)
    )


def export_to_sqlite(storage: ProxyStorage, settings: Settings, db_path: str):
    # Check if the SQLite database already exists. If not, create it.
    if not os.path.exists(db_path):
        open(db_path, "w").close()

    if not os.access(db_path, os.W_OK):
        raise PermissionError(f"No write permission for the SQLite database: {db_path}")

    engine = create_engine(f"sqlite:///{db_path}")

    # Check if 'proxies' table exists, and create it if not.
    inspector = inspect(engine)
    if not inspector.has_table("proxies"):
        Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Using sessions to manage database transactions.
    with session.begin():
        session.execute(text("CREATE TEMPORARY TABLE temp_proxies AS SELECT * FROM proxies WHERE 0"))

        if settings.enable_geolocation:
            fs.add_permission(GEODB_PATH, stat.S_IRUSR)
            mmdb: maxminddb.Reader | NullContext = maxminddb.open_database(GEODB_PATH)
        else:
            mmdb = NullContext()

        with mmdb as mmdb_reader:
            for proxy in sorted(storage, key=sort.timeout_sort_key):
                geo_data = (
                    mmdb_reader.get(proxy.exit_ip) if mmdb_reader is not None and proxy.exit_ip is not None else None
                )

                proxy_db = ProxyDB(
                    protocol=proxy.protocol.name.lower(),
                    host=proxy.host,
                    port=proxy.port,
                    username=proxy.username,
                    password=proxy.password,
                    timeout=proxy.timeout,
                    exit_ip=proxy.exit_ip,
                    last_checked=proxy.last_checked,
                    city=geo_data.get("city", {}).get("names", {}).get("en", None),
                    continent_name=geo_data.get("continent", {}).get("names", {}).get("en", None),
                    continent_code=geo_data.get("continent", {}).get("code", None),
                    country_name=geo_data.get("country", {}).get("names", {}).get("en", None),
                    country_code=geo_data.get("country", {}).get("iso_code", None),
                    latitude=geo_data.get("location", {}).get("latitude", None),
                    longitude=geo_data.get("location", {}).get("longitude", None),
                    time_zone=geo_data.get("location", {}).get("time_zone", None),
                )
                session.execute(
                    text("""
                            INSERT INTO temp_proxies (
                                protocol, host, port, username, password, timeout, exit_ip, last_checked, city,
                                continent_name, continent_code, country_name, country_code, latitude, longitude,
                                time_zone
                                )
                            VALUES (
                                :protocol, :host, :port, :username, :password, :timeout, :exit_ip, :last_checked,
                                :city, :continent_name, :continent_code, :country_name, :country_code, :latitude,
                                :longitude, :time_zone)
                        """),
                    proxy_db.__dict__,
                )

        session.execute(text("DELETE FROM proxies"))
        session.execute(text("INSERT INTO proxies SELECT * FROM temp_proxies"))
        session.execute(text("DROP TABLE temp_proxies"))

    session.close()
    engine.dispose()


def export_to_json(storage: ProxyStorage, settings: Settings) -> None:
    if settings.enable_geolocation:
        fs.add_permission(GEODB_PATH, stat.S_IRUSR)
        mmdb: maxminddb.Reader | NullContext = maxminddb.open_database(GEODB_PATH)
    else:
        mmdb = NullContext()

    with mmdb as mmdb_reader:
        proxy_dicts = [
            {
                "protocol": proxy.protocol.name.lower(),
                "username": proxy.username,
                "password": proxy.password,
                "host": proxy.host,
                "port": proxy.port,
                "exit_ip": proxy.exit_ip,
                "timeout": round(proxy.timeout, 2) if proxy.timeout is not None else None,
                "last_checked": proxy.last_checked.isoformat() if proxy.last_checked is not None else None,
                "geolocation": mmdb_reader.get(proxy.exit_ip)
                if mmdb_reader is not None and proxy.exit_ip is not None
                else None,
            }
            for proxy in sorted(storage, key=sort.timeout_sort_key)
        ]
        for path, indent, separators in (
            (settings.output_path / "proxies.json", None, (",", ":")),
            (settings.output_path / "proxies_pretty.json", "\t", None),
        ):
            path.unlink(missing_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(proxy_dicts, f, ensure_ascii=False, indent=indent, separators=separators)


def export_to_txt(storage: ProxyStorage, settings: Settings) -> None:
    sorted_proxies = sorted(storage, key=settings.sorting_key)
    grouped_proxies = tuple((k, sorted(v, key=settings.sorting_key)) for k, v in storage.get_grouped().items())
    for folder, anonymous_only in (
        (settings.output_path / "proxies", False),
        (settings.output_path / "proxies_anonymous", True),
    ):
        try:
            rmtree(folder)
        except FileNotFoundError:
            pass
        folder.mkdir()
        text = _create_proxy_list_str(proxies=sorted_proxies, anonymous_only=anonymous_only, include_protocol=True)
        (folder / "all.txt").write_text(text, encoding="utf-8")
        for proto, proxies in grouped_proxies:
            text = _create_proxy_list_str(proxies=proxies, anonymous_only=anonymous_only, include_protocol=False)
            (folder / f"{proto.name.lower()}.txt").write_text(text, encoding="utf-8")


def save_proxies(*, settings: Settings, storage: ProxyStorage) -> None:
    if settings.output_json:
        export_to_json(storage, settings)

    if settings.output_sqlite:
        db_path = settings.output_path / "proxies.sqlite3"
        export_to_sqlite(storage=storage, settings=settings, db_path=str(db_path))

    if settings.output_txt:
        export_to_txt(storage, settings)

    if IS_DOCKER:
        _logger.info("Proxies have been saved to ./out (%s in container)", settings.output_path.absolute())
    else:
        _logger.info("Proxies have been saved to %s", settings.output_path.absolute())


if __name__ == "__main__":
    print(TYPE_CHECKING)
