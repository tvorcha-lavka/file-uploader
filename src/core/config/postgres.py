from pydantic.v1 import BaseSettings


class PostgresSettings(BaseSettings):
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def POSTGRES_URL(self) -> str:  # noqa
        prefix = "postgresql+psycopg2://"
        database = self.POSTGRES_DB
        user = self.POSTGRES_USER
        password = self.POSTGRES_PASSWORD
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        return f"{prefix}{user}:{password}@{host}:{port}/{database}"


pg_settings = PostgresSettings()
