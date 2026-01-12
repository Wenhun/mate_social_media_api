import time

from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs) -> str | None:
        self.stdout.write("Waiting from db...")

        db_conn = None

        while not db_conn:
            try:
                db_conn = connections["default"]
            except OperationalError:
                self.stdout.write("DB unavailable, waiting 1 second...")
                time.sleep(1)

            self.stdout.write(self.style.SUCCESS("Database available"))
