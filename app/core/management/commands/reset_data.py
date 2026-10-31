from django.core.management.base import BaseCommand
from core import models as core_models
from django.db import transaction


class Command(BaseCommand):
    help = 'Populate COA'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            client = core_models.Client.objects.filter(
                id=1
            ).first()
            core_models.Accounts.objects.filter(
                client=client
            ).update(balance=0)

            core_models.AROINV.objects.filter(
                client=client
            ).delete()

            core_models.AROCRM.objects.filter(
                client=client
            ).delete()

            core_models.APOINV.objects.filter(
                client=client
            ).delete()

            core_models.APOCRM.objects.filter(
                client=client
            ).delete()

            core_models.INCPAY.objects.filter(
                client=client
            ).delete()

            core_models.OUTPAY.objects.filter(
                client=client
            ).delete()

            core_models.RecTrans.objects.filter(
                client=client
            ).delete()

            core_models.OJDT.objects.filter(
                client=client
            ).delete()

            core_models.OJDTTemp.objects.filter(
                client=client
            ).delete()
