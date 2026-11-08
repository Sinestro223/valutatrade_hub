import json
from pathlib import Path
from typing import Any


def load_records(filepath: Path) -> list[dict[str, Any]]:
    """Загрузка записей из JSON-файла

    Args:
        filepath (Path): путь к файлу

    Returns:
        list[dict[str, Any]]: записи или пустой список при отсутствии файла
    """
    try:
        with filepath.open(encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_records(filepath: Path, records: list[dict[str, Any]]) -> None:
    """Сохранение записей в JSON-файл

    Args:
        filepath (Path): путь к файлу
        records (list[dict[str, Any]]): записи для сохранения
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open('w', encoding='utf-8') as file:
        json.dump(records, file)
