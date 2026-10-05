from channels.generic.websocket import AsyncWebsocketConsumer
import json


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_uuid = self.scope['url_route']['kwargs']['room_uuid']
        self.room_group_uuid = f'room_{self.room_uuid}'

        await self.channel_layer.group_add(
            self.room_group_uuid,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_uuid,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            await self.channel_layer.group_send(
                self.room_group_uuid,
                {
                    'type': 'broadcast_bytes',
                    'data': bytes_data,
                    'sender_channel': self.channel_name,
                }
            )

    async def broadcast_bytes(self, event):
        if event.get('sender_channel') != self.channel_name:
            await self.send(bytes_data=event['data'])

    async def room_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message,
        }))