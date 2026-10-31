# your_app/management/commands/setup_periodic_tasks.py

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks'

    def handle(self, *args, **options):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        task_name = 'Check for recurring A/R'

        print("I Trigger task. Haha")

        task_obj, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'interval': schedule,
                'task': 'administration.tasks.recur_ar',
                'kwargs': json.dumps({})
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" created.'
            ))
        else:
            task_obj.task = 'administration.tasks.recur_ar'
            task_obj.save()
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" updated.'
            ))

        task_name_ap = 'Check for recurring A/P'

        task_obj, created = PeriodicTask.objects.get_or_create(
            name=task_name_ap,
            defaults={
                'interval': schedule,
                'task': 'administration.tasks.recur_ap',
                'kwargs': json.dumps({})
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" created.'
            ))
        else:
            task_obj.task = 'administration.tasks.recur_ap'
            task_obj.save()
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" updated.'
            ))

        task_name_ar_ap = 'Check for Open Recurring'

        task_obj, created = PeriodicTask.objects.get_or_create(
            name=task_name_ar_ap,
            defaults={
                'interval': schedule,
                'task': 'administration.tasks.close_recur',
                'kwargs': json.dumps({})
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" created.'
            ))
        else:
            task_obj.task = 'administration.tasks.close_recur'
            task_obj.save()
            self.stdout.write(self.style.SUCCESS(
                f'Task "{task_name}" updated.'
            ))
