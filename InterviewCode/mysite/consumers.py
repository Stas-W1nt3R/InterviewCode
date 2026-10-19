from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import RoomParticipant
from .code_runner import run_code, stop_code, is_running
import asyncio
import json


@database_sync_to_async
def is_user_participant_in_room(room_uuid, user_id):
    return RoomParticipant.objects.filter(room__uuid=room_uuid, user_id=user_id).exists()


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_uuid = self.scope['url_route']['kwargs']['room_uuid']
        self.room_group_uuid = f'room_{self.room_uuid}'

        if not self.scope['user'].is_authenticated:
            await self.close(code=401)
            return

        if not await is_user_participant_in_room(self.room_uuid, self.scope['user'].id):
            await self.close(code=403)
            return

        await self.channel_layer.group_add(
            self.room_group_uuid,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_uuid'):
            await self.channel_layer.group_discard(
                self.room_group_uuid,
                self.channel_name
            )

    async def receive(self, bytes_data=None):
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


class RunConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_uuid = self.scope['url_route']['kwargs']['room_uuid']
        self.room_group_uuid = f'run_{self.room_uuid}'

        if not self.scope['user'].is_authenticated:
            await self.close(code=401)
            return

        if not await is_user_participant_in_room(self.room_uuid, self.scope['user'].id):
            await self.close(code=403)
            return

        await self.channel_layer.group_add(
            self.room_group_uuid,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_uuid'):
            await self.channel_layer.group_discard(
                self.room_group_uuid,
                self.channel_name
            )

    async def run_job(self, code):
        gen = run_code(code, self.room_uuid)
        try:
            while True:
                res = await asyncio.to_thread(next, gen, None)
                if res is None:
                    break

                await self.channel_layer.group_send(
                    self.room_group_uuid,
                        {
                        "type": "run_output",
                        "data": res
                         }
                    )

        finally:
            await self.channel_layer.group_send(
                self.room_group_uuid,
                {
                    "type": "run_finished",
                }
            )

    async def run_output(self, event):
        await self.send(text_data=json.dumps({'type': 'run_output', 'data': event['data']}))

    async def run_finished(self, event):
        await self.send(text_data=json.dumps({'type': 'run_finished'}))

    async def receive(self, text_data=None):
        if text_data:
            message = json.loads(text_data)

            if message['type'] == 'run':
                if not is_running(self.room_uuid):
                    code = message['code']
                    self.run_task = asyncio.create_task(self.run_job(code))

            elif message['type'] == 'stop':
                await asyncio.to_thread(stop_code, self.room_uuid)