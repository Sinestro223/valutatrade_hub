import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .infra.constants import (
    ACTIONS_LOG_FILE,
    LOG_BACKUP_COUNT,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    LOG_MAX_BYTES,
)
from .infra.settings import SettingsLoader

actions_logger = logging.getLogger('valutatrade_hub.actions')


def configure_logging() -> None:
    """Настройка файлового журнала сделок с ротацией"""
    settings = SettingsLoader()
    filepath = Path(settings.get('actions_log_file', ACTIONS_LOG_FILE)).resolve()
    actions_logger.setLevel(settings.get('log_level', 'INFO'))
    actions_logger.propagate = False

    for handler in actions_logger.handlers[:]:
        if isinstance(handler, RotatingFileHandler):
            if handler.baseFilename == str(filepath):
                return
            actions_logger.removeHandler(handler)
            handler.close()

    filepath.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        filepath,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
        delay=True,
    )
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    actions_logger.addHandler(handler)
