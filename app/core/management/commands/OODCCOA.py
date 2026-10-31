from django.core.management.base import BaseCommand
from core import models as core_models
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Populate COA'

    def handle(self, *args, **kwargs):
        file = open('core/management/json/OODCCOA.json').read()
        json_data = json.loads(file)

        for data in json_data:
            with transaction.atomic():
                client = core_models.Client.objects.filter(
                    id=int(data.get('client'))
                ).first()
                category = core_models.AccCateg.objects.filter(
                    id=int(data.get('category'))
                ).first()

                account = core_models.Accounts(
                    client=client,
                    category=category,
                    code=data.get('code'),
                    name=data.get('name'),
                    cash=True if data.get('cash') == "Y" else False,
                    wtax=True if data.get('wtax') == "Y" else False,
                    parent=data.get('parent'),
                    type=data.get('type'),
                    level=data.get('level'),
                    balance=data.get('balance')
                )
                account.save()

                print(f"COA - {data.get('name')} Added!")
