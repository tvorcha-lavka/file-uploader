from pathlib import Path, PurePosixPath
from uuid import UUID

from pydantic import BaseModel


class UploadFilesToS3(BaseModel):
    """
    Data Transfer Object
    for uploading files to S3 task.
    """

    aws_s3_folder: PurePosixPath
    processed_files_dir: Path
    product_id: UUID


class SaveProductImagesToDB(BaseModel):
    """
    Data Transfer Object
    for saving product images to DB task.
    """

    processed_files_dir: Path
    product_id: UUID
