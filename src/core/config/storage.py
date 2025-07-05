from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    ENV_STATE: str = "development"
    AWS_S3_BUCKET_NAME: str = "tvorcha-lavka"
    AWS_S3_CUSTOM_DOMAIN: str = f"{AWS_S3_BUCKET_NAME}.s3.amazonaws.com"

    MAX_COUNT_PER_REQUEST: int = 32
    CONTENT_TYPE_MAP: dict[str, str] = {".jpg": "image/jpeg", ".webp": "image/webp"}

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        case_sensitive=True,
    )


storage_settings = StorageSettings()
