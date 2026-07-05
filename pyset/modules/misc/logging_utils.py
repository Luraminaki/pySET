#!/usr/bin/env python3
"""Shared logging setup for the pySET launcher scripts."""

import logging
import os
from logging.handlers import RotatingFileHandler

from pyset.modules.misc import logreset

_DEFAULT_MAX_BYTES = 5 * 1024 * 1024
_DEFAULT_BACKUP_COUNT = 5


def configure_launcher_logging(
    logger: logging.Logger,
    log_file_stem: str,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    backup_count: int = _DEFAULT_BACKUP_COUNT,
) -> None:
    """Initialize logging consistently across launcher scripts.

    The log file is named ``<log_file_stem>-<pid>.log``, one per OS process, rather than one
    shared file: ``RotatingFileHandler``'s rotation (renaming the file once it grows past
    `max_bytes`) is not safe across multiple processes -- if two processes hold the same file
    open, one process rotating it can orphan the other's file handle, silently dropping its log
    lines from then on. This only matters once something runs more than one worker process (e.g.
    gunicorn with `workers > 1`); a single process just gets a log file named after its own PID.
    Each file still rotates on its own, keeping up to `backup_count` older files
    (`<log_file_stem>-<pid>.log.1`, `.2`, ...) before the oldest is discarded.

    Args:
        logger (logging.Logger): The logger instance to configure.
        log_file_stem (str): The stem for the log file name.
        max_bytes (int, optional): Size in bytes a log file may reach before it
            rolls over. Defaults to 5 MiB.
        backup_count (int, optional): Number of rotated log files to keep. Defaults to 5.
    """
    logreset.reset_logging()

    level = logging.INFO
    log_file = f'{log_file_stem}-{os.getpid()}.log'
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(process)s] [%(name)s] [%(levelname)s]: %(funcName)s -- %(message)s',
        handlers=[
            RotatingFileHandler(log_file, mode='a', maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'),
            logging.StreamHandler(),
        ],
    )
    logger.setLevel(level)
