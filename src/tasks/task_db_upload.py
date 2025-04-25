from logging import getLogger

from celery import Task  # type: ignore

from core.exceptions import DatabaseError
from main import app
from processors import DBUploadProcessor

from .schemas import NotifyUserAboutProductUpload, SaveProductImagesToDB

logger = getLogger("celery.db.upload")


@app.task(name="upload.db.product.images", queue="database.queue", bind=True, max_retries=3)
def save_product_images_to_db_task(self: Task, json_str: str) -> None:
    """Saves product images to database."""
    # Validate the data
    data = SaveProductImagesToDB.model_validate_json(json_str)

    # Initialize the processor
    processor = DBUploadProcessor(data.processed_files_dir, data.product_id)

    try:
        # Execute process
        product = processor.upload()

        # Clean up the processed files after upload is done
        processor.cleanup()
    except DatabaseError as e:
        raise self.retry(exc=e)

    # Preparing data to transfer to the next task
    notify_dto = NotifyUserAboutProductUpload(
        user_id=product.owner_id,
        product_id=product.id,
        message="Product uploaded successfully!",
        status="success",
    )

    # Call the next task
    app.send_task(
        name="notify.user.product.uploaded",
        queue="notify.queue",
        kwargs={"json_str": notify_dto.model_dump_json()},
    )
