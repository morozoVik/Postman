import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Ожидание подключения к базе данных PostgreSQL"""

    help = "Ожидание подключения к базе данных"

    def handle(self, *args, **options):
        self.stdout.write("Ожидание подключения к базе данных...")

        for i in range(30):
            try:
                connections["default"].cursor()
                self.stdout.write(self.style.SUCCESS("База данных доступна!"))
                return
            except OperationalError:
                self.stdout.write(
                    f"Attempt {i + 1}/30: База данных недоступна, ожидание..."
                )
                time.sleep(2)

        self.stdout.write(self.style.ERROR("Не удалось подключиться к базе данных"))
