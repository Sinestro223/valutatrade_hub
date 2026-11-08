import os
from dataclasses import dataclass, field
from pathlib import Path

from ..core.constants import RATES_FILE
from ..infra.settings import SettingsLoader


@dataclass(frozen=True)
class ParserConfig:
    """Настройки сервиса парсинга курсов"""

    coingecko_url: str = 'https://api.coingecko.com/api/v3/simple/price'
    exchangerate_url: str = 'https://v6.exchangerate-api.com/v6'
    base_currency: str = 'USD'
    fiat_currencies: tuple[str] = ('EUR', 'GBP', 'RUB')
    crypto_id_map: dict[str, str] = field(default_factory=lambda: {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
    })
    request_timeout: float = 10
    rates_file: Path = field(
        default_factory=lambda: Path(SettingsLoader().get('rates_file', RATES_FILE)),
    )
    history_file: Path = Path('data/exchange_rates.json')
    coingecko_api_key: str = field(
        default_factory=lambda: os.getenv('COINGECKO_API_KEY', ''),
        repr=False,
    )
    exchangerate_api_key: str = field(
        default_factory=lambda: os.getenv('EXCHANGERATE_API_KEY', ''),
        repr=False,
    )
