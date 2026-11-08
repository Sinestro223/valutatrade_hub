import datetime
from secrets import token_hex

from .constants import EXCHANGE_RATES, PORTFOLIOS_FILE, USERS_FILE
from .models import Portfolio, User, Wallet
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
    values = portfolio.get_wallet_values(base_currency)
    rows = [
        (code, wallet.balance, values[code])
        for code, wallet in portfolio.wallets.items()
    ]
    return rows, sum(values.values())


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


def get_rate_to_usd(currency_code: str) -> float:
    """Получение курса валюты к USD

    Args:
        currency_code (str): код валюты

    Returns:
        float: курс к USD
    """
    if currency_code not in EXCHANGE_RATES:
        raise ValueError(f"Не удалось получить курс для '{currency_code}' к USD")
    return EXCHANGE_RATES[currency_code]


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
    currency_code = currency_code.strip().upper()
    rate = get_rate_to_usd(currency_code)
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
    currency_code = currency_code.strip().upper()
    rate = get_rate_to_usd(currency_code)
    portfolio = load_portfolio(user)
    wallet = portfolio.get_wallet(currency_code)
    if wallet is None:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    old_balance = wallet.balance
    wallet.withdraw(amount)
    save_portfolio(portfolio)
    return rate, old_balance, wallet.balance, amount * rate
