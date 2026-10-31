from core import models as core_models
from decimal import Decimal, ROUND_HALF_UP
import string
import random
# from itertools import count
# import string
# import random
# from rest_framework import (
#     status
# )
# from rest_framework.response import Response
# from django.db.models import Q
# import requests
# from django.conf import settings
# from core import models as core_m


class Core():

    @classmethod
    def generate_int(cls, length):
        return ''.join(random.choice(
            string.digits
        ) for _ in range(length))

    @classmethod
    def get_user(cls, **kwargs):

        if not kwargs:
            return core_models.UserAccount.objects.all()

        return core_models.UserAccount.objects.filter(
            **kwargs
        )

    @classmethod
    def get_bp(cls, **kwargs):

        if not kwargs:
            return core_models.BusinessPartner.objects.all()

        return core_models.BusinessPartner.objects.filter(
            **kwargs
        )

    @classmethod
    def get_acc(cls, id):
        return core_models.Accounts.objects.filter(
            id=int(id)
        ).first()

    @classmethod
    def get_ae(cls, **kwargs):
        return core_models.AutoEntries.objects.filter(
            **kwargs
        ).first()

    @classmethod
    def get_cust(cls, id):
        return core_models.BusinessPartner.objects.filter(
            id=id
        ).first()

    @classmethod
    def get_prod(cls, id):
        return core_models.Inventory.objects.filter(
            id=id
        ).first()

    @classmethod
    def add_JE(cls, ojdt, account, debit, credit,
               remarks, post_date, customer):
        jdt1 = core_models.JDT1(
            je=ojdt,
            account=account,
            code=account.code,
            name=account.name,
            debit=debit,
            credit=credit,
            remarks=remarks,
            post_date=post_date
        )
        if customer != "":
            jdt1.bp = cls.get_cust(int(customer))
        jdt1.save()

    @classmethod
    def add_JETemp(cls, ojdt, account, debit, credit,
                   remarks, post_date, customer):
        jdt1 = core_models.JDT1Temp(
            je=ojdt,
            account=account,
            code=account.code,
            name=account.name,
            debit=debit,
            credit=credit,
            remarks=remarks,
            post_date=post_date
        )
        if customer != "":
            jdt1.bp = cls.get_cust(int(customer))
        jdt1.save()

    @classmethod
    def round2(cls, value):
        if value in (None, "", "None"):
            value = 0

        clean_value = str(value).replace(",", "")

        return Decimal(clean_value).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @classmethod
    def round0(cls, value):
        if not value:
            return 0

        try:
            return int(
                Decimal(str(value).replace(",", "")).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
        except Exception:
            return 0

    @classmethod
    def add_notif(cls, client, sender, receiver, message, module, type):
        noti = core_models.Notifications(
            client=client,
            receiver=receiver,
            message=message,
            module=module,
            type=type
        )
        if sender:
            noti.sender = sender
        noti.save()
