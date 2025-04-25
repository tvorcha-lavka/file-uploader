from pathlib import Path
from uuid import UUID

from pydantic import BaseModel


class UploadFilesToS3(BaseModel):
    """
    Data Transfer Object
    for uploading files to S3 task.
    """

    processed_files_dir: Path
    product_id: UUID


class SaveProductImagesToDB(BaseModel):
    """
    Data Transfer Object
    for saving product images to DB task.
    """

    processed_files_dir: Path
    product_id: UUID


class NotifyUserAboutProductUpload(BaseModel):
    """
    Data Transfer Object
    for notifying user about product upload task.
    """

    user_id: UUID
    product_id: UUID
    message: str
    status: str
