from re import compile
from uuid import UUID

from core.config.storage import storage_settings as settings


def generate_s3_key(product_id: UUID | str, file_name: str) -> str:
    """Removes the file priority in the file name and returns the S3 key."""
    pattern = compile(r"^(original|\d+x\d+)_(\d+)_(.+)$")

    if not (match := pattern.match(file_name)):
        raise ValueError(f"Invalid file name: {file_name}; Expected file name pattern: '{pattern.pattern}'")

    prefix, _, suffix = match.groups()
    new_file_name = f"{prefix}_{suffix}"

    return str(settings.BASE_UPLOAD_DIR / str(product_id) / new_file_name)
