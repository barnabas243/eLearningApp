import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.tasks import save_message_to_db
from .models import ChatRoom
from eLearning.models import Enrollment
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("reached the chatconsumer")
        # Check if the user is authenticated
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        
        print("self.scope['user']: ",self.scope['user'])
        if isinstance(self.scope['user'], AnonymousUser):
            print("Anonymous Users are not allowed")
            await self.close(code=4003)
            return
        
        print("successful auth")
        # the room is tied to the course
        print("check course")
        self.course = await self.get_course_for_room()
        if not self.course:
            await self.close(code=4004)
            return
        print("successful course")
        
        # Check if the user is authorized to access the chat room
        print("authorizing...")
        authorized = await self.is_user_authorized()
        if not authorized:
            await self.close(code=4001)
            return
        print("authorized.")
        await self.accept()

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Parse the received JSON message
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Save the message to the database
        await self.save_message(message)

        # Broadcast the message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message
            }
        )

    async def chat_message(self, event):
        # Retrieve the message from the event
        message = event['message']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
        
    @database_sync_to_async
    def is_user_authorized(self):
        # Get the user associated with the WebSocket connection
        user = self.scope['user']
        
        # Check if the user is enrolled in the course
        is_enrolled = Enrollment.is_student_enrolled(user,self.course)
        print("is_enrolled: ",is_enrolled)
        # Check if the user is the teacher of the course
        is_teacher = self.course.teacher.username == user
        print("is_teacher: ",is_teacher)
        # User is authorized if they are enrolled in the course or if they are the teacher
        return is_enrolled or is_teacher
    
    @database_sync_to_async
    def get_course_for_room(self):
        # Retrieve the course associated with the room
        # You need to determine the course based on the room name or some other identifier
        # For example, you can query the database to find the course associated with the room name
        # Adjust this logic based on your requirements
        try:
            # Example: Querying the Course model based on the room name
            room = ChatRoom.objects.get(name=self.room_name)
            return room.course
        except ChatRoom.DoesNotExist:
            return None
    
    async def save_message(self, message):
        # Parse the received JSON message
        text_data_json = json.loads(message)

        # Extract necessary data from the message
        chat_room_id = text_data_json.get('chat_room_id')
        user_id = text_data_json.get('user_id')
        content = text_data_json.get('content')

        # Check if there are files to upload
        if 'files' in text_data_json:
            files = text_data_json['files']
            # Process and upload files (implement your logic here)
            # For example, you can save files to the media directory and store their paths in the database

        # Create a dictionary with message data
        message_data = {
            'chat_room_id': chat_room_id,
            'user_id': user_id,
            'content': content
        }

        # Call Celery task to save the message to the database asynchronously
        save_message_to_db.delay(message_data)
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.contrib.auth.models import User
# from django.contrib.sessions.models import Session
# from django.utils import timezone


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         print('self.scope["user"]: ',self.scope["user"])
#         username = self.scope["user"]
#         if username == "AnonymousUser":
#             self.close()
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = f"chat_{self.room_name}"

#         # Join room group
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]

#         # Send message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name, {"type": "chat.message", "message": message}
#         )

#     # Receive message from room group
#     async def chat_message(self, event):
#         message = event["message"]

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({"message": message}))