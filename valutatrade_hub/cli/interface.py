import argparse
import shlex

from ..core.usecases import login, register


def main() -> None:
    """Запуск интерфейса"""
    parser = argparse.ArgumentParser(prog='valutatrade-hub', add_help=False)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('register', 'login'):
        command_parser = commands.add_parser(command, add_help=False)
        command_parser.add_argument('--username', required=True)
        command_parser.add_argument('--password', required=True)

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
            else:
                current_user = login(args.username, args.password)
                print(f"Вы вошли как '{current_user.username}'")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        except (ValueError, OSError) as error:
            print(error)
