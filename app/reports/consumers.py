# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json


class UpdateNotif(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"notif_{self.user_id}"
        # self.group_name = "notif_2"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print("WebSocket disconnected:", close_code)
        print("WebSocket disconnected1:", self.group_name)

    async def receive(self, text_data):
        print("Received from client:", text_data)
        # Echo back if needed
        await self.send(text_data=json.dumps({
            "echo": text_data
        }))

    # This is called when group_send is triggered
    async def send_notif_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
