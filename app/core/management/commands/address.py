from django.core.management.base import BaseCommand
from core import models as core_models
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Populate RequestType model'

    def handle(self, *args, **options):
        region = open('core/management/json/regions.json').read()
        json_region = json.loads(region)

        for data in json_region:
            with transaction.atomic():
                create_region = core_models.Region(
                    name=data['name'],
                    region_id=data['region_id']
                )

                create_region.save()

                print(f"Region Successfully Added - {data['name']}")

        province = open('core/management/json/provinces.json').read()
        json_province = json.loads(province)

        for data in json_province:
            with transaction.atomic():
                create_province = core_models.Province(
                    region=core_models.Region.objects.filter(
                        id=data['region']
                    ).first(),
                    name=data['name']
                )

                create_province.save()

                print(f"Province Successfully Added - {data['name']}")

        municipality = open('core/management/json/municipalities.json').read()
        json_municipality = json.loads(municipality)

        for data in json_municipality:
            with transaction.atomic():
                create_municipality = core_models.Municipality(
                    province=core_models.Province.objects.filter(
                        id=data['province']
                    ).first(),
                    name=data['name']
                )

                create_municipality.save()

                print(f"Municipality Successfully Added - {data['name']}")

        barangay = open('core/management/json/barangays.json').read()
        json_barangay = json.loads(barangay)

        for data in json_barangay:
            with transaction.atomic():
                create_barangay = core_models.Barangay(
                    municipality=core_models.Municipality.objects.filter(
                        id=data['city']
                    ).first(),
                    name=data['name']
                )

                create_barangay.save()

                print(f"Barangay Successfully Added - {data['name']}")
