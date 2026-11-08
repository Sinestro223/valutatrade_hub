import tomllib
from typing import Any

from .constants import SETTINGS_FILE


class SettingsLoader:
    """Загрузка и хранение настроек приложения"""

    _instance = None

    def __new__(cls):
        """Получение единственного экземпляра"""
        if cls._instance is None:
            instance = super().__new__(cls)
            try:
                with SETTINGS_FILE.open('rb') as file:
                    config = tomllib.load(file)
            except FileNotFoundError:
                config = {}
            instance._settings = config.get('tool', {}).get('valutatrade', {})
            cls._instance = instance
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения настройки

        Args:
            key (str): имя настройки
            default (Any): значение по умолчанию

        Returns:
            Any: значение настройки
        """
        return self._settings.get(key, default)
