import math
from abc import ABC, abstractmethod
from typing import Any

import requests

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """Клиент источника курсов валют"""

    source: str

    def __init__(self, config: ParserConfig) -> None:
        """Создание клиента с настройками парсера"""
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """Получение курсов в формате валютных пар"""

    def request_json(
            self,
            url: str,
            params: dict[str, str] | None = None,
            headers: dict[str, str] | None = None,
        ) -> dict[str, Any]:
        """Получение JSON от источника курсов"""
        try:
            response = requests.get(
                url, params=params, headers=headers,
                timeout=self.config.request_timeout,
            )
        except requests.Timeout:
            raise ApiRequestError(f'{self.source}: время ожидания истекло') from None
        except requests.RequestException:
            raise ApiRequestError(f'{self.source}: ошибка сети') from None

        status = response.status_code
        if status in (401, 403):
            raise ApiRequestError(f'{self.source}: проверьте API-ключ (HTTP {status})')
        if status == 429:
            raise ApiRequestError(f'{self.source}: превышен лимит запросов (HTTP 429)')
        if not 200 <= status < 300:
            raise ApiRequestError(f'{self.source}: ошибка HTTP {status}')

        try:
            data = response.json()
        except ValueError:
            raise ApiRequestError(f'{self.source}: ответ не в формате JSON') from None
        if not isinstance(data, dict):
            raise ApiRequestError(f'{self.source}: некорректный формат ответа')
        return data

    def read_rate(self, value: Any, pair: str) -> float:
        """Проверка курса валютной пары"""
        if type(value) in (int, float):
            try:
                rate = float(value)
            except OverflowError:
                rate = math.inf
            if math.isfinite(rate) and rate > 0:
                return rate
        raise ApiRequestError(f'{self.source}: некорректный курс {pair}')


class CoinGeckoClient(BaseApiClient):
    """Получение курсов криптовалют из CoinGecko"""

    source = 'CoinGecko'

    def fetch_rates(self) -> dict[str, float]:
        """Получение курсов криптовалют к базовой валюте"""
        if not self.config.coingecko_api_key:
            raise ApiRequestError(f'{self.source}: задайте COINGECKO_API_KEY')

        base = self.config.base_currency
        data = self.request_json(
            self.config.coingecko_url,
            params={
                'ids': ','.join(self.config.crypto_id_map.values()),
                'vs_currencies': base.lower(),
            },
            headers={'x-cg-demo-api-key': self.config.coingecko_api_key},
        )
        rates = {}
        for code, coin_id in self.config.crypto_id_map.items():
            pair = f'{code}_{base}'
            prices = data.get(coin_id)
            if not isinstance(prices, dict):
                raise ApiRequestError(f'{self.source}: нет данных для {pair}')
            rates[pair] = self.read_rate(prices.get(base.lower()), pair)
        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Получение фиатных курсов из ExchangeRate-API"""

    source = 'ExchangeRate-API'

    def fetch_rates(self) -> dict[str, float]:
        """Получение фиатных курсов к базовой валюте"""
        if not self.config.exchangerate_api_key:
            raise ApiRequestError(f'{self.source}: задайте EXCHANGERATE_API_KEY')

        base = self.config.base_currency
        url = (
            f'{self.config.exchangerate_url}/'
            f'{self.config.exchangerate_api_key}/latest/{base}'
        )
        data = self.request_json(url)
        if data.get('result') != 'success':
            reason = {
                'invalid-key': 'проверьте API-ключ',
                'inactive-account': 'аккаунт не активирован',
                'quota-reached': 'превышен лимит запросов',
            }.get(str(data.get('error-type')), 'сервис вернул ошибку')
            raise ApiRequestError(f'{self.source}: {reason}')

        conversion_rates = data.get('conversion_rates')
        if data.get('base_code') != base or not isinstance(conversion_rates, dict):
            raise ApiRequestError(f'{self.source}: некорректный формат ответа')

        rates = {}
        for code in self.config.fiat_currencies:
            pair = f'{code}_{base}'
            rate = self.read_rate(conversion_rates.get(code), pair)
            rates[pair] = self.read_rate(1 / rate, pair)
        return rates
