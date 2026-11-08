from pathlib import Path

USERS_FILE = Path('data/users.json')
PORTFOLIOS_FILE = Path('data/portfolios.json')

MIN_PASSWORD_LENGTH = 4

EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 1.08,
    'GBP': 1.25,
    'RUB': 0.01,
    'BTC': 59300.0,
    'ETH': 3720.0,
    'SOL': 150.0,
}

RATES_FILE = Path('data/rates.json')
RATES_TTL_SECONDS = 300
