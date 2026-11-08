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
    PARSER_LOG_FILE,
)
from .infra.settings import SettingsLoader

actions_logger = logging.getLogger('valutatrade_hub.actions')


def configure_logging() -> None:
    """Настройка файлового журнала сделок с ротацией"""
    settings = SettingsLoader()
    level = settings.get('log_level', 'INFO')
    actions_path = Path(settings.get('actions_log_file', ACTIONS_LOG_FILE))
    parser_path = Path(settings.get('parser_log_file', PARSER_LOG_FILE))
    configure_file_logger(actions_logger, actions_path, level)
    parser_logger = logging.getLogger('valutatrade_hub.parser_service')
    configure_file_logger(parser_logger, parser_path, level)


def configure_file_logger(
        logger: logging.Logger,
        filepath: Path,
        level: str,
    ) -> None:
    """Настройка журнала с ротацией по размеру"""
    filepath = filepath.resolve()
    logger.setLevel(level)
    logger.propagate = False

    for handler in logger.handlers[:]:
        if isinstance(handler, RotatingFileHandler):
            if handler.baseFilename == str(filepath):
                return
            logger.removeHandler(handler)
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
    logger.addHandler(handler)
