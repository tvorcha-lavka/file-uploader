from contextlib import nullcontext
from uuid import UUID

import pytest
from celery import states  # type: ignore
from celery.exceptions import Retry  # type: ignore
from pytest_mock import MockerFixture

from core.exceptions import NoProcessedImageFiles, UploadingError
from processors import S3UploadProcessor
from tasks import upload_processed_images_to_s3_task
from tasks.schemas import SaveProductImagesToDB, UploadFilesToS3


class TestUploadFilesToS3Task:

    @pytest.fixture(autouse=True)
    def setup(self, s3_upload_processor: S3UploadProcessor) -> None:
        self.processor = s3_upload_processor

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "data_to_process, exception, expected_exception",
        [
            (None, None, None),
            (True, None, None),
            (True, NoProcessedImageFiles, None),
            (True, UploadingError, Retry),
        ],
    )
    def test_upload_files_task(
        self,
        mocker: MockerFixture,
        data_to_process: bool | None,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Success case of test upload files task."""
        # Patch `upload` method to not call the real logic
        upload_mock = mocker.patch.object(S3UploadProcessor, "upload", side_effect=exception)

        # Preparing data to transfer to the task
        upload_dto = UploadFilesToS3(
            processed_files_dir=self.processor.processed_files_dir,
            product_id=UUID(self.processor.product_id),
        )

        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            # Call the task
            result = upload_processed_images_to_s3_task.apply_async(
                queue="file-uploader.s3.queue",
                kwargs={"json_str": upload_dto.model_dump_json() if data_to_process else None},
            )

        if expected_exception:
            return

        if not data_to_process:
            assert result.result is None
            return

        # Check that the `upload` method has been called
        upload_mock.assert_called_once_with()

        # Check that the task completed successfully
        assert result.status == states.SUCCESS

        if isinstance(result.result, str):
            # Preparing data to transfer to the next task
            next_task_data = SaveProductImagesToDB(
                processed_files_dir=upload_dto.processed_files_dir,
                product_id=upload_dto.product_id,
            )
            assert result.result == next_task_data.model_dump_json()
        else:
            assert result.result is None
