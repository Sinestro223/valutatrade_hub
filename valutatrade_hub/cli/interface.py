import argparse
import shlex

from ..core.usecases import buy, login, register, sell, show_portfolio


def main() -> None:
    """Запуск интерфейса"""
    parser = argparse.ArgumentParser(prog='valutatrade-hub', add_help=False)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('register', 'login'):
        command_parser = commands.add_parser(command, add_help=False)
        command_parser.add_argument('--username', required=True)
        command_parser.add_argument('--password', required=True)

    portfolio_parser = commands.add_parser('show-portfolio', add_help=False)
    portfolio_parser.add_argument('--base', default='USD')

    for command in ('buy', 'sell'):
        command_parser = commands.add_parser(command, add_help=False)
        command_parser.add_argument('--currency', required=True)
        command_parser.add_argument('--amount', required=True, type=float)

    current_user = None
    while True:
        try:
            tokens = shlex.split(input('> '))
            if not tokens:
                continue
            if tokens == ['exit']:
                return

            try:
                args = parser.parse_args(tokens)
            except SystemExit:
                continue

            if args.command == 'register':
                user = register(args.username, args.password)
                print(
                    f"Пользователь '{user.username}' зарегистрирован "
                    f'(id={user.user_id}). '
                    f'Войдите: login --username {shlex.quote(user.username)} '
                    '--password ****'
                )
            elif args.command == 'login':
                current_user = login(args.username, args.password)
                print(f"Вы вошли как '{current_user.username}'")
            elif args.command == 'show-portfolio':
                if current_user is None:
                    print('Сначала выполните login')
                    continue

                base_currency = args.base.strip().upper()
                rows, total = show_portfolio(current_user, base_currency)
                print(
                    f"Портфель пользователя '{current_user.username}' "
                    f'(база: {base_currency}):'
                )
                if not rows:
                    print('Портфель пуст')
                    continue

                for code, balance, value in rows:
                    print(f'- {code}: {balance:g} -> {value:,.2f} {base_currency}')
                print('---------------------------------')
                print(f'ИТОГО: {total:,.2f} {base_currency}')
            elif args.command in ('buy', 'sell'):
                if current_user is None:
                    print('Сначала выполните login')
                    continue

                code = args.currency.strip().upper()
                if args.command == 'buy':
                    rate, old_balance, balance, value = buy(
                        current_user, code, args.amount,
                    )
                    operation = 'Покупка'
                    label = 'Оценочная стоимость покупки'
                else:
                    rate, old_balance, balance, value = sell(
                        current_user, code, args.amount,
                    )
                    operation = 'Продажа'
                    label = 'Оценочная выручка'
                print(
                    f'{operation} выполнена: {args.amount:g} {code} '
                    f'по курсу {rate:.2f} USD/{code}'
                )
                print(f'- {code}: было {old_balance:g} -> стало {balance:g}')
                print(f'{label}: {value:,.2f} USD')
        except (EOFError, KeyboardInterrupt):
            print()
            return
        except (ValueError, OSError) as error:
            print(error)
