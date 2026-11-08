import datetime

from ..core.currencies import CURRENCIES, CryptoCurrency, get_currency
from ..core.rates import load_rates
from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import RatesStorage, parse_timestamp
from .updater import RatesUpdater


def update_rates(source: str | None = None) -> tuple[int, list[str]]:
    """Обновление курсов из выбранного источника или всех источников

    Args:
        source (str | None): код источника или None для всех

    Returns:
        tuple[int, list[str]]: количество обновленных пар и ошибки источников
    """
    config = ParserConfig()
    client_types = {'coingecko': CoinGeckoClient, 'exchangerate': ExchangeRateApiClient}
    if source is not None:
        if source not in client_types:
            raise ValueError(f'Неизвестный источник курсов: {source}')
        client_types = {source: client_types[source]}

    clients = [client(config) for client in client_types.values()]
    storage = RatesStorage(config.rates_file, config.history_file)
    return RatesUpdater(clients, storage).run_update()


def show_rates(
        currency: str | None = None,
        top: int | None = None,
        base: str = 'USD',
    ) -> list[tuple[str, float, datetime.datetime]]:
    """Получение курсов из локального кеша

    Args:
        currency (str | None): код валюты для фильтрации
        top (int | None): количество самых дорогих криптовалют
        base (str): базовая валюта

    Returns:
        list[tuple[str, float, datetime.datetime]]: пары, курсы и время обновления
    """
    if top is not None and top <= 0:
        raise ValueError('Значение --top должно быть положительным')

    pairs = load_rates()
    if not pairs:
        raise ValueError("Локальный кеш курсов пуст. Выполните 'update-rates'")

    base = get_currency(base).code
    base_rate = 1.0
    base_updated_at = None
    if base != 'USD':
        base_record = pairs.get(f'{base}_USD')
        if base_record is None:
            raise ValueError(f"Курс для '{base}' не найден в кеше")
        base_rate = base_record['rate']
        base_updated_at = parse_timestamp(base_record['updated_at'])

    if currency is not None:
        currency = currency.strip().upper()
        if f'{currency}_USD' not in pairs:
            raise ValueError(f"Курс для '{currency}' не найден в кеше")

    rows = []
    for pair, record in pairs.items():
        code, _, quote = pair.partition('_')
        if quote != 'USD' or (currency is not None and code != currency):
            continue
        if top is not None and not isinstance(CURRENCIES.get(code), CryptoCurrency):
            continue
        updated_at = parse_timestamp(record['updated_at'])
        if base_updated_at is not None:
            updated_at = min(updated_at, base_updated_at)
        rows.append((f'{code}_{base}', record['rate'] / base_rate, updated_at))

    if top is not None:
        return sorted(rows, key=lambda row: (-row[1], row[0]))[:top]
    return sorted(rows)
