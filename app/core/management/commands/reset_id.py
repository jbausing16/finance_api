from django.core.management.base import BaseCommand
from core.models import Accounts as table
from django.db import connection


class Command(BaseCommand):
    help = 'Reset ID to 1 for YourModel'

    def handle(self, *args, **kwargs):
        self.stdout.write('Deleting all entries in YourModel...')
        table.objects.all().delete()

        table_name = table._meta.db_table

        sequence_name = f"{table_name}_id_seq"

        self.stdout.write('Resetting the primary key sequence...')
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1;")

        self.stdout.write(self.style.SUCCESS('Successfully reset ID to 1'))
