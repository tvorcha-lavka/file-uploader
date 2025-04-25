from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config.postgres import pg_settings

engine = create_engine(pg_settings.POSTGRES_URL, echo=False)
session_factory = sessionmaker(engine, expire_on_commit=False)
