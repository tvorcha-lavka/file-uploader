from contextlib import nullcontext
from uuid import UUID

import pytest
from celery import states  # type: ignore
from celery.exceptions import Retry  # type: ignore
from pytest_mock import MockerFixture

from core.exceptions import NoProcessedImageFiles, UploadingError
from main import app
from processors import S3UploadProcessor
from tasks import upload_processed_images_to_s3_task
from tasks.schemas import SaveProductImagesToDB, UploadFilesToS3


class TestUploadFilesToS3Task:

    @pytest.fixture(autouse=True)
    def setup(self, s3_upload_processor: S3UploadProcessor) -> None:
        self.processor = s3_upload_processor

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "exception, expected_exception, should_call_next_task",
        [
            (None, None, True),
            (NoProcessedImageFiles, None, False),
            (UploadingError, Retry, False),
        ],
    )
    def test_upload_files_task(
        self,
        mocker: MockerFixture,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
        should_call_next_task: bool,
    ) -> None:
        """Success case of test upload files task."""
        # Patch `upload` method to not call the real logic
        upload_mock = mocker.patch.object(S3UploadProcessor, "upload", side_effect=exception)
        next_task_call = mocker.patch.object(app, "send_task")

        # Preparing data to transfer to the task
        upload_dto = UploadFilesToS3(
            processed_files_dir=self.processor.processed_files_dir,
            product_id=UUID(self.processor.product_id),
        )

        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            # Call the task
            result = upload_processed_images_to_s3_task.apply_async(
                queue="upload.queue",
                kwargs={"json_str": upload_dto.model_dump_json()},
            )

        if not expected_exception:
            # Check that the `upload` method has been called
            upload_mock.assert_called_once_with()

            # Check that the task completed successfully
            assert result.status == states.SUCCESS

            if should_call_next_task:
                # Preparing data to transfer to the next task
                save_dto = SaveProductImagesToDB(
                    processed_files_dir=upload_dto.processed_files_dir,
                    product_id=upload_dto.product_id,
                )
                # Check that the next task has been called with the correct arguments
                next_task_call.assert_called_once_with(
                    name="upload.db.product.images",
                    queue="database.queue",
                    kwargs={"json_str": save_dto.model_dump_json()},
                )
            else:
                # Check that the next task has not been called
                next_task_call.assert_not_called()
        else:
            # Check that the next task has not been called
            next_task_call.assert_not_called()
