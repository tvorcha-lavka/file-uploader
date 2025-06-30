from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    DB: str = "postgres"
    USER: str = "postgres"
    PASSWORD: str = "postgres"
    HOST: str = "localhost"
    PORT: int = 5432

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        case_sensitive=True,
    )

    @property
    def POSTGRES_URL(self) -> str:  # noqa
        prefix = "postgresql+psycopg2://"
        return f"{prefix}{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"


pg_settings = PostgresSettings()
