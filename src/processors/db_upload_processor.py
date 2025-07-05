from logging import getLogger
from pathlib import Path
from re import match
from shutil import rmtree
from uuid import UUID

from sqlalchemy.exc import DBAPIError
from uuid6 import uuid7

from core.exceptions import DatabaseError
from core.session import session_factory
from models.image import ProductImageModel
from utils import log_param

logger = getLogger("celery.db.upload")


class DBUploadProcessor:

    __slots__ = (
        "processed_files_dir",
        "product_id",
    )

    def __init__(self, processed_files_dir: Path, product_id: UUID) -> None:
        self.processed_files_dir = processed_files_dir
        self.product_id = product_id

    def upload(self) -> None:
        """Extract images from the directory and uploads metadata to DB."""
        logger.debug("Upload product images to db... %s", log_param("Product ID", self.product_id))

        try:
            with session_factory() as session:
                # Extract original images
                images = self._extract_original_images()

                # Add to session
                session.add_all(images)

                # Commit
                session.commit()

        except DBAPIError as e:
            raise DatabaseError(e)

        logger.debug("Product images uploaded!  %s", log_param("Product ID", self.product_id))

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

    def _extract_original_images(self) -> list[ProductImageModel]:
        """
        Extracts original images from the directory and returns a
        list of database prepared objects.
        """
        return [
            ProductImageModel(
                id=uuid7(),
                hash=r.group(2),
                priority=int(r.group(1)),
                product_id=self.product_id,
            )
            for file in self.processed_files_dir.iterdir()
            if (r := match(r"original_(\d+)_(.+)", file.stem))
        ]
