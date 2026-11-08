import datetime
import json
import math
from pathlib import Path
from typing import Any

from ..infra.settings import SettingsLoader
from .constants import RATES_FILE, RATES_TTL_SECONDS
from .exceptions import ApiRequestError


def load_rates() -> dict[str, Any]:
    """Загрузка пар из кеша курсов

    Returns:
        dict[str, Any]: записи курсов по парам валют
    """
    filepath = Path(SettingsLoader().get('rates_file', RATES_FILE))
    try:
        with filepath.open(encoding='utf-8') as file:
            return json.load(file).get('pairs', {})
    except FileNotFoundError:
        return {}


def get_rate_to_usd(
        currency_code: str,
        pairs: dict[str, Any],
        now: datetime.datetime,
    ) -> tuple[float, datetime.datetime | None]:
    """Получение свежего курса валюты к USD

    Args:
        currency_code (str): код валюты
        pairs (dict[str, Any]): записи курсов
        now (datetime.datetime): время проверки курса

    Returns:
        tuple[float, datetime.datetime | None]: курс и время обновления
    """
    if currency_code == 'USD':
        return 1.0, None

    pair = f'{currency_code}_USD'
    if pair not in pairs:
        raise ApiRequestError(
            f"Не удалось получить курс для '{currency_code}' к USD. "
            "Обновите кеш курсов"
        )

    record = pairs[pair]
    updated_at = datetime.datetime.fromisoformat(record['updated_at'])
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=datetime.UTC)

    ttl = SettingsLoader().get('rates_ttl_seconds', RATES_TTL_SECONDS)
    if now - updated_at >= datetime.timedelta(seconds=ttl):
        raise ApiRequestError(f'Курс {pair} устарел. Обновите кеш курсов')

    rate = record['rate']
    if type(rate) not in (int, float) or rate <= 0 or not math.isfinite(rate):
        raise ApiRequestError(f'Некорректный курс {pair}. Обновите кеш курсов')
    return float(rate), updated_at


def get_cross_rate(
        from_currency: str,
        to_currency: str,
        pairs: dict[str, Any],
        now: datetime.datetime,
    ) -> tuple[float, datetime.datetime | None]:
    """Расчет курса между двумя валютами через USD

    Args:
        from_currency (str): код исходной валюты
        to_currency (str): код целевой валюты
        pairs (dict[str, Any]): записи курсов
        now (datetime.datetime): время проверки курсов

    Returns:
        tuple[float, datetime.datetime | None]: курс и время самой старой записи
    """
    if from_currency == to_currency:
        return 1.0, None

    from_rate, from_updated_at = get_rate_to_usd(from_currency, pairs, now)
    to_rate, to_updated_at = get_rate_to_usd(to_currency, pairs, now)
    dates = [date for date in (from_updated_at, to_updated_at) if date is not None]
    return from_rate / to_rate, min(dates, default=None)
