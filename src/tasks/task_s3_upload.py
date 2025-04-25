from logging import getLogger

from celery import Task  # type: ignore

from core.exceptions import NoProcessedImageFiles, UploadingError
from main import app
from processors import S3UploadProcessor

from .schemas import (
    SaveProductImagesToDB,
    UploadFilesToS3,
)

logger = getLogger("celery.s3.upload")


@app.task(name="upload.s3.product.images", queue="upload.queue", bind=True, max_retries=3)
def upload_processed_images_to_s3_task(self: Task, json_str: str) -> None:
    """Uploads processed images to S3."""
    # Validate the data
    data = UploadFilesToS3.model_validate_json(json_str)

    # Initialize the processor
    processor = S3UploadProcessor(data.processed_files_dir, data.product_id)

    try:
        # Execute process
        processor.upload()
    except UploadingError as e:
        raise self.retry(exc=e)

    except NoProcessedImageFiles:
        return

    # Preparing data to transfer to the next task
    save_dto = SaveProductImagesToDB(
        processed_files_dir=data.processed_files_dir,
        product_id=data.product_id,
    )

    # Call the next task
    app.send_task(
        name="upload.db.product.images",
        queue="database.queue",
        kwargs={"json_str": save_dto.model_dump_json()},
    )
