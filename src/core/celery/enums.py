from enum import StrEnum


class QueueEnum(StrEnum):
    FILE_UPLOADER_DB = "file-uploader.db.queue"
    FILE_UPLOADER_S3 = "file-uploader.s3.queue"
