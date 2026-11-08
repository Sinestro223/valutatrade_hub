from pathlib import Path
from typing import Any, Self

from ..core.constants import PORTFOLIOS_FILE, USERS_FILE
from ..core.utils import load_records, save_records
from .settings import SettingsLoader


class DatabaseManager:
    """Доступ к json файлам пользователей и портфелей"""

    _instance = None

    def __new__(cls) -> Self:
        """Получение единственного экземпляра"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_users(self) -> list[dict[str, Any]]:
        """Загрузка записей пользователей

        Returns:
            list[dict[str, Any]]: записи пользователей
        """
        filepath = Path(SettingsLoader().get('users_file', USERS_FILE))
        return load_records(filepath)

    def save_users(self, users: list[dict[str, Any]]) -> None:
        """Сохранение записей пользователей

        Args:
            users (list[dict[str, Any]]): записи пользователей
        """
        filepath = Path(SettingsLoader().get('users_file', USERS_FILE))
        save_records(filepath, users)

    def load_portfolios(self) -> list[dict[str, Any]]:
        """Загрузка записей портфелей

        Returns:
            list[dict[str, Any]]: записи портфелей
        """
        filepath = Path(SettingsLoader().get('portfolios_file', PORTFOLIOS_FILE))
        return load_records(filepath)

    def save_portfolios(self, portfolios: list[dict[str, Any]]) -> None:
        """Сохранение записей портфелей

        Args:
            portfolios (list[dict[str, Any]]): записи портфелей
        """
        filepath = Path(SettingsLoader().get('portfolios_file', PORTFOLIOS_FILE))
        save_records(filepath, portfolios)
