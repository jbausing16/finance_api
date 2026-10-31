from django.core.management.base import BaseCommand
from core import models as core_models
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Initial Data'

    def handle(self, *args, **kwargs):
        file = open('core/management/json/roles.json').read()
        json_data = json.loads(file)

        for data in json_data:
            with transaction.atomic():
                client = core_models.Client.objects.filter(
                    id=int(data.get('client'))
                ).first()
                roles = core_models.Roles(
                    client=client,
                    name=data.get("name"),
                )
                roles.save()

        fileType = open('core/management/json/userTypes.json').read()
        jsonType = json.loads(fileType)

        for data in jsonType:
            with transaction.atomic():
                types = core_models.Types(
                    name=data.get("name"),
                )
                types.save()

        fileapproval = open('core/management/json/approvals.json').read()
        jsonApproval = json.loads(fileapproval)

        for data in jsonApproval:
            client = core_models.Client.objects.filter(
                    id=int(data.get('client'))
                ).first()
            with transaction.atomic():
                app = core_models.Approval(
                    client=client,
                    module=data.get("module"),
                )
                app.save()

        fileAutomatic = open(
            'core/management/json/automaticEntries.json').read()
        jsonAutomatic = json.loads(fileAutomatic)

        for data in jsonAutomatic:
            client = core_models.Client.objects.filter(
                    id=int(data.get('client'))
                ).first()
            with transaction.atomic():
                auto = core_models.AutoEntries(
                    client=client,
                    module=data.get("module"),
                    type=data.get("type"),
                )
                auto.save()

        filedocuNo = open(
                'core/management/json/documentNo.json').read()
        jsondocuNo = json.loads(filedocuNo)

        for data in jsondocuNo:
            client = core_models.Client.objects.filter(
                    id=int(1)
                ).first()
            with transaction.atomic():
                docno = core_models.DocumentNo(
                    client=client,
                    name=data.get("name"),
                    no=data.get("no"),
                )
                docno.save()

        fileaccType = open(
                'core/management/json/accCateg.json').read()
        jsonccType = json.loads(fileaccType)

        for data in jsonccType:
            client = core_models.Client.objects.filter(
                    id=int(1)
                ).first()
            with transaction.atomic():
                docno = core_models.AccCateg(
                    client=client,
                    name=data.get("name"),
                )
                docno.save()
