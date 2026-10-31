# signals.py
from django.db.models.signals import post_save  # post_delete, pre_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.models import Notifications
import pytz


channel_layer = get_channel_layer()

# @receiver(post_save, sender=Event)
# def event_saved(sender, instance, created, **kwargs):
#     print("Signal fired for Event:", instance.id)
#     event = c_m.Event.objects.get(id=instance.id)
#     serializer = e_ser.EventSerializer(
#         instance=event,
#         many=False
#     )
#     async_to_sync(channel_layer.group_send)(
#         "events_group",
#         {
#             "type": "send_event_update",
#             "data": {
#                 "event": "update",
#                 "id": instance.id,
#                 "data": serializer.data,
#             }
#         }
#     )


# @receiver(post_save, sender=Attendees)
# def attendee_saved(sender, instance, created, **kwargs):
#     print("Signal fired for Atendee - Event:", instance.id)
#     event = instance.event
#     count = Attendees.objects.filter(event=event).count()
#     async_to_sync(channel_layer.group_send)(
#         "events_group",
#         {
#             "type": "send_event_update",
#             "data": {
#                 "event": "update_attendee",
#                 "id": event.id,
#                 "count": count,
#             }
#         }
#     )

#     serializer = e_ser.AttendeeSerializer(instance=instance, many=False)
#     async_to_sync(channel_layer.group_send)(
#         "attendee_group",
#         {
#             "type": "send_attendee_update",
#             "data": {
#                 "event": "new_attendee" if created else "update_attendee",
#                 "id": instance.id,
#                 "event_id": instance.event.id,
#                 "data": serializer.data,
#             }
#         }
#     )


@receiver(post_save, sender=Notifications)
def notif_saved(sender, instance, created, **kwargs):
    print("Signal fired for Notif:", instance.id)
    manila_tz = pytz.timezone('Asia/Manila')
    # notif = c_m.Notifications.objects.get(id=instance.id)
    time = instance.date_added.astimezone(manila_tz)

    # sid = notif.sender.id
    rid = instance.receiver.id
    group_name = f"notif_{rid}"
    # group_name = "notif_101_102"
    print(f"Group Name: {group_name}")
    print(f"Instance {instance}")

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notif_update",
            "data": {
                "event": "notifications",
                "id": instance.id,
                "date": time.date().isoformat(),
                "time": time.time().isoformat(),
                "message": instance.message,
                "read": 2,
                "site": instance.module,
                "type": instance.type
            }
        }
    )


# @receiver(post_save, sender=Notifications)
# def notif_saved(sender, instance, created, **kwargs):
#     print("Signal fired for Notif:", instance)

#     manila_tz = pytz.timezone('Asia/Manila')
#     time = instance.created_at

#     if not is_aware(time):
#         time = make_aware(time)
#     time = time.astimezone(manila_tz)

#     cover = ""
#     if instance.event.cover:
#         cover = instance.event.cover.url

#     async_to_sync(channel_layer.group_send)(
#         "notif_group",
#         {
#             "type": "send_notif_update",
#             "data": {
#                 "event": "update_notif",
#                 "id": instance.id,
#                 "name": instance.event.name,
#                 "message": instance.message,
#                 "photo": cover,
#                 "site": instance.event.website,
#                 "read": 1 if instance.read else 2,
#                 "date": time.strftime('%Y-%m-%d'),
#                 "time": time.strftime('%H:%M:%S'),
#                 "cid": instance.client.id
#             }
#         }
#     )


# @receiver(pre_save, sender=User)
# def detect_password_change(sender, instance, **kwargs):
#     if instance.pk:
#         old_user = sender.objects.get(pk=instance.pk)

#         if old_user.password != instance.password:
#             print("Password changed")
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)(
#                 "user_group",
#                 {
#                     "type": "send_user_update",
#                     "data": {
#                         "event": "password_changed",
#                         "id": instance.pk,
#                     }
#                 }
#             )


# @receiver(post_delete, sender=Event)
# def event_deleted(sender, instance, **kwargs):
#     print("Signal fired for Event deletion:", instance.id)
#     async_to_sync(channel_layer.group_send)(
#         "events_group",
#         {
#             "type": "send_event_update",
#             "data": {
#                 "event": "delete",
#                 "id": instance.id
#             }
#         }
#     )
