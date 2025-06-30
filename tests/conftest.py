from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from pydantic.v1 import BaseSettings
from sqlalchemy.orm import Session

from core.celery.client import app
from processors import DBUploadProcessor, S3UploadProcessor


@dataclass
class File:
    path: Path
    type: str  # noqa: VNE003


@dataclass
class ProcessedFileBound:
    original: File
    _150x200: File
    _450x600: File
    _675x900: File


class SettingsForTests(BaseSettings):
    USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")
    SESSION_ID: UUID = UUID("00000000-0000-0000-0000-000000000002")
    PRODUCT_ID: UUID = UUID("00000000-0000-0000-0000-000000000003")

    BASE_DIR: Path = Path("/") / "tmp" / "test-dir"
    PROCESSED_FILES_DIR: Path = BASE_DIR / str(USER_ID) / str(SESSION_ID) / "processed"


@pytest.fixture(scope="session")
def test_settings() -> SettingsForTests:
    return SettingsForTests()


@pytest.fixture(scope="session", autouse=True)
def configure_celery() -> None:
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


@pytest.fixture(scope="class")
def processed_files_dir(test_settings: SettingsForTests) -> Generator[Path, Any, None]:
    test_settings.PROCESSED_FILES_DIR.mkdir(parents=True, exist_ok=True)

    yield test_settings.PROCESSED_FILES_DIR

    rmtree(test_settings.BASE_DIR, ignore_errors=True)


@pytest.fixture(scope="function")
def processed_files(processed_files_dir: Path) -> Generator[ProcessedFileBound, Any, None]:
    dimensions = ("original", "150x200", "450x600", "675x900")
    file_types = ("jpg", "webp", "webp", "webp")
    mime_types = ("image/jpeg", "image/webp", "image/webp", "image/webp")
    file_hash = "0000000000000000"

    files = tuple(
        File(path=processed_files_dir / f"{size}_0_{file_hash}.{file_type}", type=mime_type)
        for size, file_type, mime_type in zip(dimensions, file_types, mime_types)
    )

    processed_files_dir.mkdir(parents=True, exist_ok=True)

    for _file_ in files:
        _file_.path.touch(exist_ok=True)

    yield ProcessedFileBound(*files)

    for file_path in processed_files_dir.iterdir() if processed_files_dir.exists() else []:
        file_path.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def mock_s3_client() -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch.object(S3UploadProcessor.session, "client") as mock_client:
        mock_client.return_value = MagicMock()
        yield mock_client.return_value


@pytest.fixture(scope="function")
def mock_alchemy_session(test_settings: SettingsForTests) -> Generator[MagicMock | AsyncMock, Any, None]:
    with patch.object(Session, "__enter__") as mock_session:
        mock_session.return_value = MagicMock()
        yield mock_session.return_value


@pytest.fixture(scope="class")
def s3_upload_processor(processed_files_dir: Path, test_settings: SettingsForTests) -> S3UploadProcessor:
    return S3UploadProcessor(
        processed_files_dir=processed_files_dir,
        product_id=test_settings.PRODUCT_ID,
    )


@pytest.fixture(scope="class")
def db_upload_processor(processed_files_dir: Path, test_settings: SettingsForTests) -> DBUploadProcessor:
    return DBUploadProcessor(
        processed_files_dir=processed_files_dir,
        product_id=test_settings.PRODUCT_ID,
    )
