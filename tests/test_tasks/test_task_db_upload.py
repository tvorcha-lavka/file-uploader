from contextlib import nullcontext

import pytest
from celery import states  # type: ignore
from celery.exceptions import Retry  # type: ignore
from pytest_mock import MockerFixture

from core.exceptions import DatabaseError
from main import app
from models.product import ProductModel
from processors import DBUploadProcessor
from tasks import save_product_images_to_db_task
from tasks.schemas import NotifyUserAboutProductUpload, SaveProductImagesToDB
from tests.conftest import SettingsForTests


class TestUploadFilesToDBTask:

    @pytest.fixture(autouse=True)
    def setup(self, db_upload_processor: DBUploadProcessor, test_settings: SettingsForTests) -> None:
        self.processor = db_upload_processor

        self.user_id = test_settings.USER_ID
        self.product_id = test_settings.PRODUCT_ID

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "exception, expected_exception, should_call_next_task",
        [
            (None, None, True),
            (DatabaseError, Retry, False),
        ],
    )
    def test_save_product_images_to_db_task(
        self,
        mocker: MockerFixture,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
        should_call_next_task: bool,
    ) -> None:
        """Success case of test upload files task."""
        # Patch `upload` method to not call the real logic
        upload_mock = mocker.patch.object(
            DBUploadProcessor,
            "upload",
            side_effect=exception,
            return_value=ProductModel(
                id=self.product_id,
                owner_id=self.user_id,
            ),
        )
        cleanup_mock = mocker.patch.object(DBUploadProcessor, "cleanup")
        next_task_call = mocker.patch.object(app, "send_task")

        # Preparing data to transfer to the task
        save_dto = SaveProductImagesToDB(
            processed_files_dir=self.processor.processed_files_dir,
            product_id=self.processor.product_id,
        )

        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            # Call the task
            result = save_product_images_to_db_task.apply_async(
                queue="database.queue",
                kwargs={"json_str": save_dto.model_dump_json()},
            )

        if not expected_exception:
            # Check that the `upload` method has been called
            upload_mock.assert_called_once_with()

            # Check that the task completed successfully
            assert result.status == states.SUCCESS

            if should_call_next_task:
                # Preparing data to transfer to the next task
                notify_dto = NotifyUserAboutProductUpload(
                    user_id=self.user_id,
                    product_id=self.product_id,
                    message="Product uploaded successfully!",
                    status="success",
                )
                # Check that the next task has been called with the correct arguments
                next_task_call.assert_called_once_with(
                    name="notify.user.product.uploaded",
                    queue="notify.queue",
                    kwargs={"json_str": notify_dto.model_dump_json()},
                )
            else:
                # Check that cleanup and the next task has not been called
                cleanup_mock.assert_not_called()
                next_task_call.assert_not_called()
        else:
            # Check that cleanup and the next task has not been called
            cleanup_mock.assert_not_called()
            next_task_call.assert_not_called()
