import datetime
from secrets import token_hex

from .constants import PORTFOLIOS_FILE, USERS_FILE
from .models import User
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
