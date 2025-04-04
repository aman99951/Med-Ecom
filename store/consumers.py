import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage, Agent, User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"chat_{self.scope['user'].id}"
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        is_from_user = text_data_json['is_from_user']

        if is_from_user:
            agent = Agent.objects.get(is_available=True)
            ChatMessage.objects.create(
                user=self.scope['user'], agent=agent, message=message, is_from_user=True)
        else:
            user = User.objects.get(id=self.scope['user'].id)
            ChatMessage.objects.create(
                user=user, agent=self.scope['user'], message=message, is_from_user=False)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': message,
            'is_from_user': is_from_user
        })

    async def chat_message(self, event):
        message = event['message']
        is_from_user = event['is_from_user']

        await self.send(text_data=json.dumps({'message': message, 'is_from_user': is_from_user}))
