from django.core.management.base import BaseCommand
from core import models as core_models
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Populate COA'

    def handle(self, *args, **kwargs):
        file = open('core/management/json/modules.json').read()
        json_data = json.loads(file)

        for data in json_data:
            with transaction.atomic():
                que = core_models.Modules(
                    module=data.get('mod'),
                    sub_module=data.get('sub'),
                )
                que.save()

                print(f"Module - {data.get('sub')} Added!")
