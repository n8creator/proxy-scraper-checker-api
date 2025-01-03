from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ProxyModel(BaseModel):
    protocol: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: Optional[float] = None
    exit_ip: Optional[str] = None
    last_checked: Optional[datetime] = None

    city: Optional[str] = None  # city.names.en
    continent_name: Optional[str] = None  # continent.names.en
    continent_code: Optional[str] = None  # continent.code
    country_name: Optional[str] = None  # country.names.en
    country_code: Optional[str] = None  # country.iso_code
    latitude: Optional[float] = None  # location.latitude
    longitude: Optional[float] = None  # location.longitude
    time_zone: Optional[str] = None  # location.time_zone


class ProxyDB(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True)
    protocol = Column(String)
    host = Column(String)
    port = Column(Integer)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    timeout = Column(Float, nullable=True)
    exit_ip = Column(String, nullable=True)
    last_checked = Column(DateTime, nullable=True)

    city = Column(String, nullable=True)
    continent_name = Column(String, nullable=True)
    continent_code = Column(String, nullable=True)
    country_name = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    time_zone = Column(String, nullable=True)

    @classmethod
    def from_pydantic(cls, proxy: ProxyModel) -> "ProxyDB":
        return cls(
            protocol=proxy.protocol,
            host=proxy.host,
            port=proxy.port,
            username=proxy.username,
            password=proxy.password,
            timeout=proxy.timeout,
            exit_ip=proxy.exit_ip,
            last_checked=proxy.last_checked,
            city=proxy.city,
            continent_name=proxy.continent_name,
            continent_code=proxy.continent_code,
            country_name=proxy.country_name,
            country_code=proxy.country_code,
            latitude=proxy.latitude,
            longitude=proxy.longitude,
            time_zone=proxy.time_zone,
        )
