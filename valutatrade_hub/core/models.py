import datetime
import hashlib
import math

from .exceptions import InsufficientFundsError

EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 1.08,
    'GBP': 1.25,
    'RUB': 0.01,
    'BTC': 59300.0,
    'ETH': 3720.0,
    'SOL': 150.0,
}


class User:
    """Пользователь валютного кошелька"""

    def __init__(
            self,
            user_id: int,
            username: str,
            hashed_password: str,
            salt: str,
            registration_date: datetime.datetime,
        ) -> None:
        """Создание пользователя

        Args:
            user_id (int): идентификатор пользователя
            username (str): имя пользователя
            hashed_password (str): хеш пароля
            salt (str): соль для хеширования пароля
            registration_date (datetime.datetime): дата регистрации
        """
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        """ID пользователя"""
        return self._user_id

    @property
    def username(self) -> str:
        """Имя пользователя"""
        return self._username

    @username.setter
    def username(self, new_username: str) -> None:
        """Изменение имени пользователя

        Args:
            new_username (str): новое имя пользователя
        """
        if not new_username.strip():
            raise ValueError('Имя пользователя не может быть пустым')
        self._username = new_username

    @property
    def hashed_password(self) -> str:
        """Хеш пароля"""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Соль для хеширования пароля"""
        return self._salt

    @property
    def registration_date(self) -> datetime.datetime:
        """Дата регистрации пользователя"""
        return self._registration_date

    def get_user_info(self) -> dict[str, int | str | datetime.datetime]:
        """Получение информации о пользователе

        Returns:
            dict[str, int | str | datetime.datetime]: данные пользователя без пароля
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'registration_date': self.registration_date,
        }

    def change_password(self, new_password: str) -> None:
        """Изменение пароля пользователя

        Args:
            new_password (str): новый пароль
        """
        if len(new_password) < 4:
            raise ValueError('Пароль не может быть короче 4 символов')
        if self.verify_password(new_password):
            raise ValueError('Пароль не может совпадать с текущим')

        self._hashed_password = self._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверка пароля пользователя

        Args:
            password (str): пароль для проверки

        Returns:
            bool: совпадает ли пароль с текущим
        """
        return self._hash_password(password) == self._hashed_password

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля с солью пользователя

        Args:
            password (str): пароль для хеширования

        Returns:
            str: хеш пароля
        """
        return hashlib.sha256((password + self._salt).encode('utf-8')).hexdigest()


class Wallet:
    """Кошелек для одной валюты"""

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        """Создание кошелька

        Args:
            currency_code (str): код валюты
            balance (float): начальный баланс
        """
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self) -> float:
        """Текущий баланс кошелька"""
        return self._balance

    @balance.setter
    def balance(self, new_balance: float) -> None:
        """Изменение баланса кошелька

        Args:
            new_balance (float): новый баланс
        """
        if not self._is_finite_number(new_balance) or new_balance < 0:
            raise ValueError('Баланс должен быть конечным неотрицательным числом')
        self._balance = float(new_balance)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса

        Args:
            amount (float): сумма пополнения
        """
        self._validate_amount(amount)
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие средств с кошелька

        Args:
            amount (float): сумма снятия
        """
        self._validate_amount(amount)
        if amount > self.balance:
            raise InsufficientFundsError(
                f'Недостаточно средств: доступно {self.balance} {self.currency_code}, '
                f'требуется {amount} {self.currency_code}'
            )
        self.balance -= amount

    def get_balance_info(self) -> dict[str, str | float]:
        """Получение информации о балансе

        Returns:
            dict[str, str | float]: код валюты и баланс
        """
        return {'currency_code': self.currency_code, 'balance': self.balance}

    def _validate_amount(self, amount: float) -> None:
        """Проверка суммы операции

        Args:
            amount (float): сумма операции
        """
        if not self._is_finite_number(amount) or amount <= 0:
            raise ValueError('Сумма должна быть конечным положительным числом')

    @staticmethod
    def _is_finite_number(value: object) -> bool:
        """Проверка числового значения

        Args:
            value (object): значение для проверки

        Returns:
            bool: является ли значение конечным числом
        """
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False


class Portfolio:
    """Портфель пользователя"""

    def __init__(
            self,
            user: User,
            wallets: dict[str, Wallet] | None = None,
        ) -> None:
        """Создание портфеля

        Args:
            user (User): владелец портфеля
            wallets (dict[str, Wallet] | None): кошельки пользователя
        """
        self._user = user
        self._user_id = user.user_id
        self._wallets = {} if wallets is None else wallets.copy()

    @property
    def user(self) -> User:
        """Пользователь портфеля

        Returns:
            User
        """
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Копия словаря кошельков

        Returns:
            dict[str, Wallet]
        """
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавление кошелька для валюты

        Args:
            currency_code (str): код валюты

        Returns:
            Wallet: новый или существующий кошелек
        """
        currency_code = currency_code.strip().upper()
        if not currency_code:
            raise ValueError('Код валюты не может быть пустым')
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)
        return self._wallets[currency_code]

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """Поиск кошелька по коду валюты

        Args:
            currency_code (str): код валюты

        Returns:
            Wallet | None: кошелек или None, если он отсутствует
        """
        return self._wallets.get(currency_code.strip().upper())

    def get_total_value(self, base_currency: str = 'USD') -> float:
        """Расчет общей стоимости портфеля

        Args:
            base_currency (str): базовая валюта

        Returns:
            float: стоимость портфеля в базовой валюте
        """
        base_currency = base_currency.strip().upper()
        if base_currency not in EXCHANGE_RATES:
            raise ValueError(f'Неизвестная базовая валюта "{base_currency}"')

        total_usd = 0.0
        for currency_code, wallet in self._wallets.items():
            if currency_code not in EXCHANGE_RATES:
                raise ValueError(f'Нет курса для валюты "{currency_code}"')
            total_usd += wallet.balance * EXCHANGE_RATES[currency_code]
        return total_usd / EXCHANGE_RATES[base_currency]
