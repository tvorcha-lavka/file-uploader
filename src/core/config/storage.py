from pathlib import Path

from pydantic.v1 import BaseSettings


class StorageSettings(BaseSettings):
    ENV_STATE: str = "development"
    AWS_S3_BUCKET_NAME: str = "tvorcha-lavka"
    AWS_S3_CUSTOM_DOMAIN: str = f"{AWS_S3_BUCKET_NAME}.s3.amazonaws.com"

    MAX_COUNT_PER_REQUEST: int = 32
    CONTENT_TYPE_MAP: dict[str, str] = {".jpg": "image/jpeg", ".webp": "image/webp"}
    BASE_UPLOAD_DIR: Path = Path() / "products" if ENV_STATE != "development" else Path() / "test" / "products"


storage_settings = StorageSettings()
