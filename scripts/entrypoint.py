#!/usr/bin/env python
"""
Development entrypoint for `file-uploader` project.

This script runs the Celery application for development purposes.
"""
from core.config.log import logging_settings as settings
from main import app


def main() -> None:
    params = [
        "worker",
        "--pool=solo",
        "--concurrency=10",
        "--queues=upload.queue,database.queue",
        "--max-tasks-per-child=50",
        "--hostname=file-uploader@%h",
        "--loglevel=%s" % settings.LOGGING_LEVEL_CONSOLE,
        "--without-mingle",
        "--without-gossip",
    ]
    app.start(params)


if __name__ == "__main__":
    main()
