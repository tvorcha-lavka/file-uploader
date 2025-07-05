from pathlib import PurePosixPath
from re import compile
from uuid import UUID


def generate_s3_key(folder: PurePosixPath, product_id: UUID | str, file_name: str) -> str:
    """Removes the file priority in the file name and returns the S3 key."""
    pattern = compile(r"^(original|\d+x\d+)_(\d+)_(.+)$")

    if not (match := pattern.match(file_name)):
        raise ValueError(f"Invalid file name: {file_name}; Expected file name pattern: '{pattern.pattern}'")

    prefix, _, suffix = match.groups()
    new_file_name = f"{prefix}_{suffix}"

    return str(folder / new_file_name).format(product_id=product_id)
