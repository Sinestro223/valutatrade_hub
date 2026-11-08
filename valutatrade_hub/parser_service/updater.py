import datetime
import logging
from collections.abc import Iterable

from ..core.exceptions import ApiRequestError
from .api_clients import BaseApiClient
from .storage import RateRecord, RatesStorage

logger = logging.getLogger(__name__)


def utc_timestamp() -> str:
    """Получение текущего времени UTC в формате ISO"""
    return datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00', 'Z')


class RatesUpdater:
    """Обновление курсов из доступных источников"""

    def __init__(
            self,
            clients: Iterable[BaseApiClient],
            storage: RatesStorage,
        ) -> None:
        """Создание сервиса обновления курсов

        Args:
            clients (Iterable[BaseApiClient]): клиенты источников курсов
            storage (RatesStorage): хранилище кеша и истории
        """
        self.clients = tuple(clients)
        self.storage = storage

    def run_update(self) -> tuple[int, list[str]]:
        """Получение и сохранение курсов из всех источников

        Returns:
            tuple[int, list[str]]: количество обновленных пар и ошибки источников
        """
        logger.info('Начинаем обновление курсов')
        records: list[tuple[str, RateRecord]] = []
        errors = []

        for client in self.clients:
            logger.info('Запрашиваем курсы у %s', client.source)
            try:
                rates = client.fetch_rates()
            except ApiRequestError as error:
                errors.append(str(error))
                logger.error(
                    'Не удалось получить курсы от %s: %s', client.source, error,
                )
                continue

            timestamp = utc_timestamp()
            records.extend(
                (pair, {'rate': rate, 'updated_at': timestamp, 'source': client.source})
                for pair, rate in rates.items()
            )
            logger.info('%s: получено курсов %d', client.source, len(rates))

        if records:
            logger.info('Сохраняем курсы в %s', self.storage.rates_file)
            updated = self.storage.save_rates(records, utc_timestamp())
        else:
            updated = 0
        logger.info('Обновление завершено. Пар: %d, ошибок: %d', updated, len(errors))
        return updated, errors
