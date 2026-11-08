from collections.abc import Callable
from functools import wraps

from .core.models import User
from .logging_config import actions_logger

TradeResult = tuple[float, float, float, float]
Trade = Callable[[User, str, float], TradeResult]


def log_action(action: str, verbose: bool = False) -> Callable[[Trade], Trade]:
    """Создание декоратора для записи сделки в журнал

    Args:
        action (str): название операции
        verbose (bool): добавлять старый и новый баланс

    Returns:
        Callable[[Trade], Trade]: декоратор сделки
    """
    def decorator(func: Trade) -> Trade:
        @wraps(func)
        def wrapper(user: User, currency_code: str, amount: float) -> TradeResult:
            currency = currency_code.strip().upper()
            context = (
                f'{action} user={user.username!r} '
                f'currency={currency!r} amount={amount}'
            )
            try:
                result = func(user, currency_code, amount)
            except Exception as error:
                actions_logger.info(
                    '%s result=ERROR error_type=%s error_message=%r',
                    context, type(error).__name__, str(error),
                )
                raise

            rate, old_balance, balance, _ = result
            message = f"{context} rate={rate:.8g} base='USD' result=OK"
            if verbose:
                message += f' old_balance={old_balance:g} balance={balance:g}'
            actions_logger.info(message)
            return result

        return wrapper

    return decorator
