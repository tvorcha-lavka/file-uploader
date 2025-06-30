from logging import getLogger
from pathlib import Path
from uuid import UUID

from boto3 import Session
from boto3.exceptions import S3UploadFailedError
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, NoCredentialsError
from gevent.pool import Pool

from core.config.storage import storage_settings as settings
from core.exceptions import NoProcessedImageFiles, UploadingError
from utils import generate_s3_key, log_param

logger = getLogger("celery.s3.upload")


class S3UploadProcessor:
    """Uploads files to S3."""

    session = Session()

    __slots__ = (
        "processed_files_dir",
        "product_id",
        "s3_bucket",
    )

    def __init__(self, processed_files_dir: Path, product_id: UUID) -> None:
        self.processed_files_dir: Path = processed_files_dir
        self.product_id: str = str(product_id)
        self.s3_bucket: str = settings.AWS_S3_BUCKET_NAME

    def has_any_processed_files(self) -> bool:
        """Checks if there are processed images available in the directory."""
        return self.processed_files_dir.exists() and any(self.processed_files_dir.iterdir())

    def upload(self) -> None:
        """Uploads processed images to S3."""
        if not self.has_any_processed_files():
            logger.info("No images to upload. %s", log_param("Product ID", self.product_id))
            raise NoProcessedImageFiles()

        try:
            return self._perform_upload()  # Upload to S3
        except (S3UploadFailedError, BotoCoreError, NoCredentialsError, RuntimeError) as e:
            logger.warning("Upload failed for product %s: %s", self.product_id, e)
            raise UploadingError(e)

    def _perform_upload(self) -> None:
        """Uploads processed images to S3 using gevent for concurrency."""
        logger.debug("Uploading images...  %s", log_param("Product ID", self.product_id))

        pool, pool_size = Pool(), settings.MAX_COUNT_PER_REQUEST
        client = self.session.client("s3", config=Config(max_pool_connections=pool_size))

        for file_path in self.processed_files_dir.iterdir():
            pool.spawn(self._upload_file, client, file_path)

        pool.join()  # Run concurrent images uploading
        logger.debug("Images are uploaded! %s", log_param("Product ID", self.product_id))

    def _upload_file(self, client: BaseClient, file_path: Path) -> None:
        """Uploads a file to S3 bucket."""
        content_type = settings.CONTENT_TYPE_MAP[file_path.suffix]
        s3_file_key = generate_s3_key(self.product_id, file_path.name)

        # Upload the image file
        logger.debug("Uploading image %s...", file_path.name)
        client.upload_file(
            Filename=file_path,
            Bucket=self.s3_bucket,
            Key=s3_file_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.debug("Image %s is uploaded!", file_path.name)
