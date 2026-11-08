import datetime
from secrets import token_hex

from .constants import PORTFOLIOS_FILE, USERS_FILE
from .currencies import get_currency
from .models import Portfolio, User, Wallet
from .rates import get_cross_rate, load_rates
from .utils import load_records, save_records


def register(username: str, password: str) -> User:
    """Регистрация пользователя с пустым портфелем

    Args:
        username (str): имя пользователя
        password (str): пароль пользователя

    Returns:
        User: зарегистрированный пользователь
    """
    username = username.strip()
    users = load_records(USERS_FILE)
    if any(record['username'] == username for record in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((record['user_id'] for record in users), default=0) + 1
    registration_date = datetime.datetime.now(datetime.UTC)
    user = User(user_id, username, '', token_hex(16), registration_date)
    user.change_password(password)

    portfolios = load_records(PORTFOLIOS_FILE)
    if not any(record['user_id'] == user_id for record in portfolios):
        portfolios.append({'user_id': user_id, 'wallets': {}})
        save_records(PORTFOLIOS_FILE, portfolios)

    users.append({
        'user_id': user.user_id,
        'username': user.username,
        'hashed_password': user.hashed_password,
        'salt': user.salt,
        'registration_date': user.registration_date.isoformat(),
    })
    save_records(USERS_FILE, users)
    return user


def login(username: str, password: str) -> User:
    """Вход пользователя по имени и паролю

    Args:
        username (str): имя пользователя
        password (str): пароль пользователя

    Returns:
        User: пользователь, который вошел в систему
    """
    username = username.strip()
    for record in load_records(USERS_FILE):
        if record['username'] == username:
            user = User(
                record['user_id'],
                record['username'],
                record['hashed_password'],
                record['salt'],
                datetime.datetime.fromisoformat(record['registration_date']),
            )
            if not user.verify_password(password):
                raise ValueError('Неверный пароль')
            return user

    raise ValueError(f"Пользователь '{username}' не найден")


def load_portfolio(user: User) -> Portfolio:
    """Загрузка портфеля пользователя

    Args:
        user (User): владелец портфеля

    Returns:
        Portfolio: портфель с сохраненными кошельками
    """
    for record in load_records(PORTFOLIOS_FILE):
        if record['user_id'] == user.user_id:
            wallets = {
                code: Wallet(code, data['balance'])
                for code, data in record['wallets'].items()
            }
            return Portfolio(user, wallets)

    raise ValueError(f"Портфель пользователя '{user.username}' не найден")


def show_portfolio(
        user: User,
        base_currency: str = 'USD',
    ) -> tuple[list[tuple[str, float, float]], float]:
    """Получение балансов и стоимости портфеля

    Args:
        user (User): владелец портфеля
        base_currency (str): базовая валюта

    Returns:
        tuple[list[tuple[str, float, float]], float]: строки портфеля и итог
    """
    portfolio = load_portfolio(user)
    base_currency = get_currency(base_currency).code
    wallets = portfolio.wallets
    pairs = load_rates()

    now = datetime.datetime.now(datetime.UTC)
    rows = []
    for code, wallet in wallets.items():
        rate, _ = get_cross_rate(code, base_currency, pairs, now)
        rows.append((code, wallet.balance, wallet.balance * rate))
    return rows, sum((value for _, _, value in rows), 0.0)


def save_portfolio(portfolio: Portfolio) -> None:
    """Сохранение кошельков пользователя

    Args:
        portfolio (Portfolio): портфель пользователя
    """
    records = load_records(PORTFOLIOS_FILE)
    for record in records:
        if record['user_id'] == portfolio.user.user_id:
            record['wallets'] = {
                code: {'balance': wallet.balance}
                for code, wallet in portfolio.wallets.items()
            }
            save_records(PORTFOLIOS_FILE, records)
            return

    raise ValueError(f"Портфель пользователя '{portfolio.user.username}' не найден")


def get_rate(
        from_currency: str,
        to_currency: str,
    ) -> tuple[float, datetime.datetime | None]:
    """Получение курса между двумя валютами

    Args:
        from_currency (str): код исходной валюты
        to_currency (str): код целевой валюты

    Returns:
        tuple[float, datetime.datetime | None]: курс и время обновления
    """
    return get_cross_rate(
        get_currency(from_currency).code,
        get_currency(to_currency).code,
        load_rates(),
        datetime.datetime.now(datetime.UTC),
    )


def buy(
        user: User,
        currency_code: str,
        amount: float,
    ) -> tuple[float, float, float, float]:
    """Покупка валюты и сохранение портфеля

    Args:
        user (User): владелец портфеля
        currency_code (str): код валюты
        amount (float): количество валюты

    Returns:
        tuple[float, float, float, float]: курс, старый и новый баланс, стоимость
    """
    rate, _ = get_rate(currency_code, 'USD')
    currency_code = currency_code.strip().upper()
    portfolio = load_portfolio(user)
    wallet = portfolio.add_currency(currency_code)
    old_balance = wallet.balance
    wallet.deposit(amount)
    save_portfolio(portfolio)
    return rate, old_balance, wallet.balance, amount * rate


def sell(
        user: User,
        currency_code: str,
        amount: float,
    ) -> tuple[float, float, float, float]:
    """Продажа валюты и сохранение портфеля

    Args:
        user (User): владелец портфеля
        currency_code (str): код валюты
        amount (float): количество валюты

    Returns:
        tuple[float, float, float, float]: курс, старый и новый баланс, выручка
    """
    rate, _ = get_rate(currency_code, 'USD')
    currency_code = currency_code.strip().upper()
    portfolio = load_portfolio(user)
    wallet = portfolio.get_wallet(currency_code)
    if wallet is None:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    old_balance = wallet.balance
    wallet.withdraw(amount)
    save_portfolio(portfolio)
    return rate, old_balance, wallet.balance, amount * rate
