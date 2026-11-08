from abc import ABC, abstractmethod
from dataclasses import dataclass

from .exceptions import CurrencyNotFoundError


@dataclass(frozen=True)
class Currency(ABC):
    """Валюта с названием и кодом"""

    name: str
    code: str

    def __post_init__(self) -> None:
        """Проверка названия и кода валюты"""
        if not self.name.strip():
            raise ValueError('Название валюты не может быть пустым')
        if not 2 <= len(self.code) <= 5 or not (
            self.code.isascii() and self.code.isalnum() and self.code.isupper()
        ):
            raise ValueError('Код валюты должен содержать от 2 до 5 символов')

    @abstractmethod
    def get_display_info(self) -> str:
        """Получение строки с информацией о валюте"""


@dataclass(frozen=True)
class FiatCurrency(Currency):
    """Фиатная валюта со страной или зоной эмиссии"""

    issuing_country: str

    def get_display_info(self) -> str:
        """Получение информации о фиатной валюте"""
        return f'[FIAT] {self.code} - {self.name} (Issuing: {self.issuing_country})'


@dataclass(frozen=True)
class CryptoCurrency(Currency):
    """Криптовалюта с алгоритмом и капитализацией"""

    algorithm: str
    market_cap: float

    def get_display_info(self) -> str:
        """Получение информации о криптовалюте"""
        return (
            f'[CRYPTO] {self.code} - {self.name} '
            f'(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})'
        )


CURRENCIES = {
    'USD': FiatCurrency('US Dollar', 'USD', 'United States'),
    'EUR': FiatCurrency('Euro', 'EUR', 'Eurozone'),
    'GBP': FiatCurrency('Pound Sterling', 'GBP', 'United Kingdom'),
    'RUB': FiatCurrency('Russian Ruble', 'RUB', 'Russia'),
    'BTC': CryptoCurrency('Bitcoin', 'BTC', 'SHA-256', 1.12e12),
    'ETH': CryptoCurrency('Ethereum', 'ETH', 'Proof of Stake', 4.0e11),
    'SOL': CryptoCurrency('Solana', 'SOL', 'Proof of History', 7.0e10),
}


def get_currency(code: str) -> Currency:
    """Получение валюты по коду

    Args:
        code (str): код валюты

    Returns:
        Currency: фиатная валюта или криптовалюта
    """
    code = code.strip().upper()
    if code not in CURRENCIES:
        raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")
    return CURRENCIES[code]
