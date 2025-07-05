from logging import getLogger

from celery import Task

from core.celery.client import app
from core.celery.enums import QueueEnum
from core.exceptions import DatabaseError
from processors import DBUploadProcessor

from .schemas import SaveProductImagesToDB

logger = getLogger("celery.db.upload")


@app.task(name="upload.db.product.images", queue=QueueEnum.FILE_UPLOADER_DB, bind=True)
def save_product_images_to_db_task(self: Task, json_str: str | None = None) -> None:
    """Saves product images to database."""
    if json_str is None:
        logger.info("No data to process")
        return

    # Validate the data
    data = SaveProductImagesToDB.model_validate_json(json_str)

    # Initialize the processor
    processor = DBUploadProcessor(
        processed_files_dir=data.processed_files_dir,
        product_id=data.product_id,
    )

    try:
        # Execute process
        processor.upload()

        # Clean up the processed files after upload is done
        processor.cleanup()

    except DatabaseError as e:
        raise self.retry(exc=e)
