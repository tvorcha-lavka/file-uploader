from logging import getLogger
from pathlib import Path
from re import match
from shutil import rmtree
from uuid import UUID

from sqlalchemy.exc import DBAPIError, NoResultFound
from uuid6 import uuid7

from core.exceptions import DatabaseError
from core.session import session_factory
from models.image import ProductImageModel, ProductImageProcessedModel
from models.product import ProductModel
from utils import generate_s3_key, log_param

logger = getLogger("celery.db.upload")

OriginalImageObjects = list[ProductImageModel]
ProcessedImageObjects = list[ProductImageProcessedModel]


class DBUploadProcessor:

    __slots__ = (
        "processed_files_dir",
        "product_id",
        "originals",
        "processed",
    )

    def __init__(self, processed_files_dir: Path, product_id: UUID) -> None:
        self.processed_files_dir = processed_files_dir
        self.product_id = product_id
        self.originals: OriginalImageObjects = []
        self.processed: ProcessedImageObjects = []

    def upload(self) -> ProductModel:
        """Extract original and processed images from the directory and uploads them to DB."""
        logger.debug("Updating product data... %s", log_param("Product ID", self.product_id))
        objects: list[ProductImageModel | ProductImageProcessedModel] = []

        try:
            with session_factory() as session:
                # Extract original and processed images
                self.originals = self._extract_original_images()
                self.processed = self._extract_processed_images()

                # Add to session
                objects.extend(self.originals)
                objects.extend(self.processed)
                session.add_all(objects)

                # Update product status
                product = session.get_one(ProductModel, self.product_id)
                product.active = True

                session.commit()

        except (DBAPIError, NoResultFound) as e:
            raise DatabaseError(e)

        logger.debug("Product data updated!  %s", log_param("Product ID", self.product_id))
        return product

    def cleanup(self) -> None:
        """Removes processed content from the directory."""
        logger.debug("Remove processed content and directory... %s", self.processed_files_dir.name)
        rmtree(self.processed_files_dir, ignore_errors=True)

        session_dir: Path = self.processed_files_dir.parent
        user_dir: Path = session_dir.parent

        # Ensure empty and remove session directory
        if session_dir.exists() and not any(session_dir.iterdir()):
            logger.debug("Remove empty session directory... %s", session_dir.name)
            session_dir.rmdir()

        # Ensure empty and remove user directory
        if user_dir.exists() and not any(user_dir.iterdir()):
            logger.debug("Remove empty user directory... %s", user_dir.name)
            user_dir.rmdir()

    def _extract_original_images(self) -> OriginalImageObjects:
        """
        Extracts original images from the directory and returns a
        list of database prepared objects.
        """
        return [
            ProductImageModel(
                id=uuid7(),
                hash=r.group(2),
                image=generate_s3_key(self.product_id, file.name),
                priority=int(r.group(1)),
                product_id=self.product_id,
            )
            for file in self.processed_files_dir.iterdir()
            if (r := match(r"original_(\d+)_(.+)", file.stem))
        ]

    def _extract_processed_images(self) -> ProcessedImageObjects:
        """
        Extracts processed images from the directory and returns a
        list of database prepared objects.
        """
        return [
            ProductImageProcessedModel(
                id=uuid7(),
                image=generate_s3_key(self.product_id, file.name),
                width=int(r.group(1)),
                height=int(r.group(2)),
                original_image_id=orig.id,
            )
            for orig in self.originals
            for file in self.processed_files_dir.iterdir()
            if (r := match(rf"(\d+)x(\d+)_(\d+)_({orig.hash})", file.stem))
        ]
