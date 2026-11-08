class InsufficientFundsError(ValueError):
    """Недостаточно средств для снятия"""


class ApiRequestError(ValueError):
    """Курс валюты недоступен"""


class CurrencyNotFoundError(ValueError):
    """Код валюты отсутствует в реестре"""
