from django.core.management.base import BaseCommand
from core import models as core_models
from django.db import transaction


class Command(BaseCommand):
    help = 'Initial Data'

    def handle(self, *args, **kwargs):
        roles = core_models.Roles.objects.all()
        modu = core_models.Modules.objects.all()

        access_list = []

        for role in roles:
            for module in modu:
                access_list.append(
                    core_models.Access(
                        role=role,
                        module=module,
                        access=True,
                        view=True,
                        create=False,
                        edit=False,
                        delete=False,
                    )
                )

        with transaction.atomic():
            core_models.Access.objects.bulk_create(access_list)
