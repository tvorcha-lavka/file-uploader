class DatabaseError(Exception):
    """Base class for database errors."""

    pass


class UploadingError(Exception):
    """Base class for upload errors."""

    pass


class NoProcessedImageFiles(Exception):
    """Raised when there are no processed image files in the directory."""

    pass
