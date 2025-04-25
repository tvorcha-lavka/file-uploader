from pathlib import Path
from shutil import copytree
from typing import Any

import pytest
from pytest_mock import MockerFixture

from main import app
from processors import DBUploadProcessor, S3UploadProcessor
from tasks.schemas import UploadFilesToS3
from tests.conftest import SettingsForTests


class TestUploadFlow:

    @pytest.fixture(autouse=True)
    def setup(self, processed_files_dir: Path, test_settings: SettingsForTests) -> None:
        copytree(Path("/tests/test_data"), processed_files_dir, dirs_exist_ok=True)
        self.files_count = len(list(processed_files_dir.iterdir()))

        self.task_dto = UploadFilesToS3(
            processed_files_dir=processed_files_dir,
            product_id=test_settings.PRODUCT_ID,
        )

    @pytest.mark.smoke
    @pytest.mark.usefixtures("mock_s3_client", "mock_alchemy_session")
    def test_upload_flow(self, mocker: MockerFixture) -> None:
        """Smoke test for upload flow."""

        def apply_async(*args: Any, **kwargs: Any) -> None:
            """Patches `send_task` method as `apply_async`."""
            if task := app.tasks.get(kwargs.pop("name", None)):
                task.apply_async(*args, **kwargs)

        # Patch task calls method `send_task` as `apply_async`
        mocker.patch.object(app, "send_task", side_effect=apply_async)

        # Create SPYs to verify that the flow methods are being called as expected
        s3_upload_file_spy = mocker.spy(S3UploadProcessor, "_upload_file")
        db_upload_spy = mocker.spy(DBUploadProcessor, "upload")
        cleanup_spy = mocker.spy(DBUploadProcessor, "cleanup")

        # Execute upload flow through the first task
        app.send_task(
            name="upload.s3.product.images",
            queue="upload.queue",
            kwargs={"json_str": self.task_dto.model_dump_json()},
        )

        # Verify that the flow methods are being called as expected
        assert s3_upload_file_spy.call_count == self.files_count
        db_upload_spy.assert_called_once()
        cleanup_spy.assert_called_once()
