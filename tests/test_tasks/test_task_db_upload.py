from contextlib import nullcontext

import pytest
from celery import states
from celery.exceptions import Retry
from pytest_mock import MockerFixture

from core.celery.enums import QueueEnum
from core.exceptions import DatabaseError
from processors import DBUploadProcessor
from tasks import save_product_images_to_db_task
from tasks.schemas import SaveProductImagesToDB
from tests.conftest import SettingsForTests


class TestUploadFilesToDBTask:

    @pytest.fixture(autouse=True)
    def setup(self, db_upload_processor: DBUploadProcessor, test_settings: SettingsForTests) -> None:
        self.processor = db_upload_processor

        self.user_id = test_settings.USER_ID
        self.product_id = test_settings.PRODUCT_ID

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "data_to_process, exception, expected_exception",
        [
            (None, None, None),
            (True, None, None),
            (True, DatabaseError, Retry),
        ],
    )
    def test_save_product_images_to_db_task(
        self,
        mocker: MockerFixture,
        data_to_process: bool | None,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Success case of test upload files task."""
        # Patch `upload` method to not call the real logic
        upload_mock = mocker.patch.object(
            DBUploadProcessor,
            "upload",
            side_effect=exception,
            return_value=None,
        )
        cleanup_mock = mocker.patch.object(DBUploadProcessor, "cleanup")

        # Preparing data to transfer to the task
        save_dto = SaveProductImagesToDB(
            processed_files_dir=self.processor.processed_files_dir,
            product_id=self.processor.product_id,
        )

        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            # Call the task
            result = save_product_images_to_db_task.apply_async(
                queue=QueueEnum.FILE_UPLOADER_DB,
                kwargs={"json_str": save_dto.model_dump_json() if data_to_process else None},
            )

        if expected_exception:
            return

        if not data_to_process:
            assert result.result is None
            return

        # Check that the `upload` method has been called
        upload_mock.assert_called_once_with()
        cleanup_mock.assert_called_once_with()

        # Check that the task completed successfully
        assert result.status == states.SUCCESS

        if isinstance(result.result, str):
            raise AssertionError("Result should be None")
        else:
            assert result.result is None
