import datetime
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, TypedDict


class RateRecord(TypedDict):
    """Запись курса для кеша"""

    rate: float
    updated_at: str
    source: str


def read_json(filepath: Path, default: Any) -> Any:
    """Чтение JSON с начальным значением для нового файла"""
    try:
        with filepath.open(encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def write_json(filepath: Path, data: Any) -> None:
    """Атомарная запись JSON через временный файл"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = NamedTemporaryFile(
        mode='w', encoding='utf-8', dir=filepath.parent, delete=False,
    )
    temp_path = Path(temp_file.name)
    try:
        with temp_file:
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
        temp_path.replace(filepath)
    finally:
        temp_path.unlink(missing_ok=True)


def parse_timestamp(value: str) -> datetime.datetime:
    """Чтение времени курса с UTC по умолчанию"""
    timestamp = datetime.datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=datetime.UTC)
    return timestamp


class RatesStorage:
    """Хранилище текущих курсов и истории"""

    def __init__(self, rates_file: Path, history_file: Path) -> None:
        """Сохранение путей к кешу и истории"""
        self.rates_file = rates_file
        self.history_file = history_file

    def save_rates(
            self,
            records: list[tuple[str, RateRecord]],
            last_refresh: str,
        ) -> int:
        """Сохранение полученных курсов и обновление кеша

        Args:
            records (list[tuple[str, RateRecord]]): пары и полученные курсы
            last_refresh (str): время завершения обновления

        Returns:
            int: количество обновленных пар в кеше
        """
        if not records:
            return 0

        cache = read_json(self.rates_file, {})
        pairs = cache.setdefault('pairs', {})
        history = read_json(self.history_file, [])
        history_ids = {record['id'] for record in history}
        updated_pairs = set()
        history_changed = False

        for pair, record in records:
            timestamp = record['updated_at']
            current = pairs.get(pair)
            if current is None or (
                parse_timestamp(timestamp) > parse_timestamp(current['updated_at'])
            ):
                pairs[pair] = record
                updated_pairs.add(pair)

            record_id = f'{pair}_{timestamp}'
            if record_id not in history_ids:
                from_currency, to_currency = pair.split('_')
                history.append({
                    'id': record_id,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'rate': record['rate'],
                    'timestamp': timestamp,
                    'source': record['source'],
                })
                history_ids.add(record_id)
                history_changed = True

        if history_changed:
            write_json(self.history_file, history)
        if updated_pairs:
            cache['last_refresh'] = last_refresh
            write_json(self.rates_file, cache)
        return len(updated_pairs)
