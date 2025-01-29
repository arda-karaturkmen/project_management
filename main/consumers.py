import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PanelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Kullanıcı bağlandığında çalışır
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
            
        await self.channel_layer.group_add(
            "panel_group",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Kullanıcı ayrıldığında çalışır
        await self.channel_layer.group_discard(
            "panel_group",
            self.channel_name
        )

    async def receive(self, text_data):
        # Kullanıcıdan mesaj geldiğinde çalışır
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Mesajı gruptaki herkese gönder
        await self.channel_layer.group_send(
            "panel_group",
            {
                'type': 'panel_message',
                'message': message,
                'user': self.scope["user"].username
            }
        )

    async def panel_message(self, event):
        # Grup mesajını kullanıcılara ilet
        message = event['message']
        user = event['user']
        
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user
        }))
