from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import BotoCoreError, NoCredentialsError
from pytest import FixtureRequest
from pytest_mock import MockerFixture

from core.exceptions import NoProcessedImageFiles, UploadingError
from processors import S3UploadProcessor
from tests.conftest import ProcessedFileBound


class TestS3UploadProcessor:

    @pytest.fixture(autouse=True)
    def setup(self, s3_upload_processor: S3UploadProcessor) -> None:
        self.test_bucket = "test_bucket"

        self.processor = s3_upload_processor
        self.processor.aws_s3_bucket = self.test_bucket

    @pytest.mark.unit
    @pytest.mark.parametrize("has_processed", (True, False))
    def test_has_any_processed_files(self, request: FixtureRequest, has_processed: bool) -> None:
        """Test has_any_processed_files method."""
        if has_processed:  # dynamically fixture
            request.getfixturevalue("processed_files")

        # Call `has_any_processed_files` method
        result = self.processor.has_any_processed_files()

        # Check result
        assert result == has_processed

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "has_any_processed_files, exception, expected_exception",
        [
            (True, None, None),  # Success, no exceptions
            (False, NoProcessedImageFiles, NoProcessedImageFiles),
            (True, S3UploadFailedError, UploadingError),
            (True, BotoCoreError, UploadingError),
            (True, NoCredentialsError, UploadingError),
            (True, RuntimeError, UploadingError),
        ],
    )
    def test_upload(
        self,
        mocker: MockerFixture,
        has_any_processed_files: bool,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Test upload method."""
        # Patch dependencies
        mocker.patch.object(S3UploadProcessor, "has_any_processed_files", return_value=has_any_processed_files)
        mocker.patch(f"{S3UploadProcessor.__module__}.logger.warning")

        # Patch `_perform_upload` method to rise exceptions
        mock_perform_upload = mocker.patch.object(S3UploadProcessor, "_perform_upload", side_effect=exception)

        # Call `upload` method and assert results
        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            self.processor.upload()

        if not expected_exception:
            if not has_any_processed_files:
                mock_perform_upload.assert_not_called()
            else:
                mock_perform_upload.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.usefixtures("processed_files")
    def test_perform_upload(
        self,
        mocker: MockerFixture,
        mock_s3_client: MagicMock,
        processed_files_dir: Path,
    ) -> None:
        """Test _perform_upload method."""
        from gevent.pool import Pool

        # Patch `spawn` and `join` methods
        mocked_spawn = mocker.patch.object(Pool, "spawn", side_effect=lambda *args: MagicMock())
        mocked_join = mocker.patch.object(Pool, "join")

        # Collect expected calls to `spawn`
        expected_calls = [
            mocker.call(self.processor._upload_file, mock_s3_client, file_path)
            for file_path in processed_files_dir.iterdir()
        ]

        # Call `_perform_upload` method
        self.processor._perform_upload()

        # Check if `spawn` was called as expected with the correct arguments
        mocked_spawn.assert_has_calls(expected_calls, any_order=False)

        # Check if `join` was called exactly once to wait for all greenlet tasks
        mocked_join.assert_called_once_with()

    @pytest.mark.unit
    def test_upload_file(
        self,
        mocker: MockerFixture,
        mock_s3_client: MagicMock,
        processed_files: ProcessedFileBound,
    ) -> None:
        """Test _upload_file method."""
        # Get test data
        test_file = processed_files._150x200
        s3_key = f"s3_key/{test_file.path.name}"

        # Patch `generate_s3_key` function
        func = f"{self.processor.__module__}.generate_s3_key"
        mock_generate_s3_key = mocker.patch(func, return_value=s3_key)

        # Call `_upload_file` method
        self.processor._upload_file(mock_s3_client, test_file.path)

        # Check if `_get_s3_key` method was called
        mock_generate_s3_key.assert_called_once()

        # Check if `upload_file` method was called
        mock_s3_client.upload_file.assert_called_once_with(
            Filename=test_file.path,
            Bucket=self.test_bucket,
            Key=s3_key,
            ExtraArgs={"ContentType": test_file.type},
        )
