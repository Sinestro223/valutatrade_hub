from pathlib import Path

SETTINGS_FILE = Path('pyproject.toml')

ACTIONS_LOG_FILE = Path('logs/actions.log')
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3
LOG_FORMAT = '%(levelname)s %(asctime)s %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
