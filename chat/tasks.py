# tasks.py
from celery import shared_task
from courses.models import User
from chat.models import Message

# @shared_task
# def save_message_to_db(message_data):
#     # Extract message data
#     chat_room_id = message_data.get('chat_room_id')
#     user_id = message_data.get('user_id')
#     content = message_data.get('content')

#     # Create a new Message object
#     message = Message(
#         chat_room_id=chat_room_id,
#         user_id=user_id,
#         content=content
#     )

#     # Save the message to the database
#     message.save()
