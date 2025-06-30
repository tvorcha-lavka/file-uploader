from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.exc import DBAPIError

from core.exceptions import DatabaseError
from models.base import BaseModel
from models.image import ProductImageModel, ProductImageProcessedModel
from processors import DBUploadProcessor


class TestDBUploadProcessor:

    @pytest.fixture(autouse=True)
    def setup(self, db_upload_processor: DBUploadProcessor) -> None:
        self.processor = db_upload_processor

    @pytest.mark.unit
    @pytest.mark.usefixtures("processed_files")
    def test_upload(self, mocker: MockerFixture, mock_alchemy_session: MagicMock) -> None:
        """Test upload method."""
        _extract_original_images = mocker.spy(DBUploadProcessor, "_extract_original_images")
        _extract_processed_images = mocker.spy(DBUploadProcessor, "_extract_processed_images")
        mocker.patch(f"{self.processor.__module__}.generate_s3_key", return_value="some_s3_key")

        def assert_func(func, db_model: type[BaseModel], expected_elements_count: int) -> None:  # type: ignore
            func.assert_called_once()
            assert isinstance(func.spy_return, list)
            assert all(isinstance(i, db_model) for i in func.spy_return)
            assert len(func.spy_return) == expected_elements_count

        # Call `upload` method
        self.processor.upload()

        # Check if `_extract_original_images` and `_extract_processed_images`
        # are called as expected and return correct data
        assert_func(_extract_original_images, ProductImageModel, 1)
        assert_func(_extract_processed_images, ProductImageProcessedModel, 3)

        # Check if `add_all` and `commit` are called as expected
        add_all_data = _extract_original_images.spy_return + _extract_processed_images.spy_return
        mock_alchemy_session.add_all.assert_called_once_with(add_all_data)
        mock_alchemy_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_upload_exception(
        self,
        mocker: MockerFixture,
        mock_alchemy_session: MagicMock,
    ) -> None:
        """Test upload method with exception."""
        mocker.patch.object(DBUploadProcessor, "_extract_original_images", return_value=[])
        mocker.patch.object(DBUploadProcessor, "_extract_processed_images", return_value=[])

        mocker.patch.object(DBAPIError, "__init__", return_value=None)
        mock_alchemy_session.commit.side_effect = DBAPIError

        with pytest.raises(DatabaseError):
            self.processor.upload()

    @pytest.mark.unit
    @pytest.mark.usefixtures("processed_files")
    def test_cleanup(self, processed_files_dir: Path) -> None:
        """Test cleanup method."""
        # Ensure the files and dirs exist before cleanup
        assert processed_files_dir.exists()
        assert any(processed_files_dir.iterdir())

        # Call the `cleanup` method
        self.processor.cleanup()

        # processed_files_dir must be deleted
        assert not self.processor.processed_files_dir.exists()

        # session_dir must be deleted as it's empty now
        session_dir = self.processor.processed_files_dir.parent
        assert not session_dir.exists()

        # user_dir must be deleted as it's also empty
        user_dir = session_dir.parent
        assert not user_dir.exists()

        # Call the `cleanup` method to test idempotency
        self.processor.cleanup()
