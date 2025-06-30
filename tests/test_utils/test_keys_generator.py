from contextlib import nullcontext
from re import compile

import pytest
from pytest import FixtureRequest

from core.config.storage import storage_settings as settings
from tests.conftest import SettingsForTests
from utils import generate_s3_key


@pytest.mark.unit
@pytest.mark.parametrize(
    "exception, expected_exception",
    [(None, None), (ValueError, ValueError)],
)
def test_generate_s3_key(
    request: FixtureRequest,
    test_settings: SettingsForTests,
    exception: type[Exception] | None,
    expected_exception: type[Exception] | None,
) -> None:
    """Test generate_s3_key function."""
    file_name = "filename.jpg"

    if not expected_exception:
        files = request.getfixturevalue("processed_files")
        file_name = files.original.path.name

    # Call `generate_s3_key` function
    with pytest.raises(expected_exception) if expected_exception else nullcontext():
        result = generate_s3_key(test_settings.PRODUCT_ID, file_name)

    if not expected_exception:
        # Manually construct expected result
        pattern = compile(r"^(original|\d+x\d+)_(\d+)_(.+)$")
        match = pattern.match(file_name)

        assert match is not None
        prefix, _, suffix = match.groups()

        # Check result
        assert result == str(settings.BASE_UPLOAD_DIR / str(test_settings.PRODUCT_ID) / f"{prefix}_{suffix}")
