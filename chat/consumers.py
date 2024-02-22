from datetime import timedelta
import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.serializers import ChatMembershipSerializer, ChatRoomSerializer, MessageSerializer
from eLearning.serializers import UserSerializer
from .models import ChatMembership, ChatRoom
from eLearning.models import Enrollment, User
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}  # maintain the connected clients without group_channels.

    async def connect(self):
        logger.info("Reached the chatconsumer")

        # Check if the user is authenticated
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        logger.debug("User: %s", self.scope["user"])
        if isinstance(self.scope["user"], AnonymousUser):
            logger.error("Anonymous Users are not allowed")
            await self.close(code=4003, reason="Anonymous Users are not allowed")
            return

        # the room is tied to the course
        logger.debug("Check course")
        self.course = await self.get_course_for_room()
        if not self.course:
            logger.error("Course not found for room")
            await self.close(code=4004, reason="Course not found for room")
            return

        logger.debug("Successful course")

        # Check if the user is authorized to access the chat room
        logger.debug("Authorizing...")
        authorized = await self.is_user_authorized()
        if not authorized:
            logger.error("User not authorized")
            await self.close(code=4001, reason="User not authorized")
            return

        logger.debug("Authorized.")

        username = self.scope["user"].username  # Assuming user ID is used as a unique identifier
        if username not in self.connected_users:
            self.connected_users[username] = []

        self.connected_users[username].append(self.room_group_name)

        await self.accept()

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def disconnect(self, close_code):
        """
        Handles the disconnection of a WebSocket connection.

        Args:
            close_code: The code indicating the reason for the disconnection.
        """
        try:
            # Log the disconnection reason code and reason text
            logger.info(f"Disconnecting WebSocket connection.")

            await self.notify_user_disconnected()

            # Remove user from connected_users
            self.remove_user_from_connected_users()

            # Leave the room group
            await self.leave_room_group()

            logger.info("WebSocket connection disconnected successfully")
        except Exception as e:
            logger.error("Failed to disconnect WebSocket connection: %s", e)
            # Handle disconnection failure

    async def notify_user_disconnected(self):
        """
        Notifies online users about the disconnection.
        """
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.user_data",
                    "action": "user_disconnected",
                    "users": self.scope["user"].username,
                },
            )
            logger.debug("User disconnected message sent successfully to room group")
        except Exception as e:
            logger.error("Failed to send user disconnected message: %s", e)
            # Handle send failure

    def remove_user_from_connected_users(self):
        """
        Removes the disconnected user from the connected_users dictionary.
        """
        try:
            username = self.scope["user"].username
            # Iterate over the list and remove all occurrences of self.room_group_name
            while self.room_group_name in self.connected_users[username]:
                self.connected_users[username].remove(self.room_group_name)
                logger.debug("User removed from self.connected_users")

        except Exception as e:
            logger.error("Failed to remove user from self.connected_users: %s", e)
            # Handle removal failure

    async def leave_room_group(self):
        """
        Leaves the room group.
        """
        try:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            logger.debug("Left the room group successfully")
        except Exception as e:
            logger.error("Failed to leave the room group: %s", e)
            # Handle leave failure

    async def receive(self, text_data):
        """
        Receives and processes incoming messages from the WebSocket connection.

        Args:
            text_data (str): The message data received from the WebSocket connection.

        Raises:
            Exception: If an error occurs during message processing.
        """
        try:
            # Parse the incoming message data as a dictionary
            message_data = json.loads(text_data)
            logger.debug("Received message_data: %s", message_data)

            # Check if the message is a request to retrieve user data
            if "action" in message_data:
                if message_data["action"] == "get_user_data":
                    logger.info("Received request to get user data")
                    logger.info("Connected users: %s", self.connected_users)
                    # Retrieve list of connected users
                    users = self.get_connected_users()
                    chat_room_id = message_data['chat_room_id']
                    
                    last_viewed_message = await self.get_last_viewed_message(chat_room_id)
                    logger.debug("Connected users: %s", users)

                    # Send user data to room group
                    await self.send_user_data(users)
                    logger.info("sending user last viewed message...")
                    
                    await self.send(text_data=json.dumps({
                        "type": "chat.user_data",
                        "action": "user_last_viewed_message",
                        "last_viewed_message": last_viewed_message
                    }))
                    logger.info("Sent user last viewed message...")
                    
                elif message_data["action"] == "close_user_connection":
                    logger.info(
                        "Received request to close %s connection to %s",
                        self.scope["user"].username,
                        self.room_group_name,
                    )

                    await self.updateLastViewedMessageId(message_data['chat_room_id'], message_data['last_viewed_message'])
                    logger.info(
                        "Completed request to close %s connection to %s",
                        self.scope["user"].username,
                        self.room_group_name,
                    )

            else:
                # Save the validated message object to the database within a transaction
                cleaned_message = await self.process_message_data(message_data)
                logger.info("this should be able to be logged")
                username = await database_sync_to_async(lambda: cleaned_message.user.username)()
                logger.info("pass username")
                full_name = await database_sync_to_async(cleaned_message.user.get_full_name)()
                logger.info("pass full_name")
                # Log the cleaned message with user data
                logger.info("cleaned message: %s, username: %s, full name: %s", username, full_name)
                                
                message = {
                            'id': cleaned_message.id,
                            "content": cleaned_message.content,
                            "username": username,  # Access the associated user's username
                            "full_name": full_name,
                            "timestamp": cleaned_message.timestamp.isoformat(),
                            # Add any other fields you want to send
                        }

                # Send the message to the room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "action": "send_message",
                        "message": message
                    },
                )
                logger.info("Message sent to room group: %s", self.room_group_name)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON message: %s", e)
            # Handle JSON decoding error
            # Example: Send an error response to the client

        except ValidationError as e:
            logger.error("Validation error while saving message: %s", e)
            # Handle validation error
            # Example: Send an error response to the client

        except Exception as e:
            logger.error("An error occurred while processing the message: %s", e)
            # Handle other exceptions
            # Example: Send an error response to the client

    async def chat_user_data(self, event):
        """
        Handles the 'chat.user_data' event.
        """
        try:
            # Retrieve user data from the event
            users = event["users"]
            action = event["action"]

            logger.info("Sending user data to client: %s", users)
            
            
            if action == "user_connected":
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "chat.user_data", 
                            "action": action, 
                            "users": users,
                            }
                    )
                )
            elif action == "user_disconnected":
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "chat.user_data", 
                            "action": action, 
                            "users": users
                            }
                    )
                )
        except Exception as e:
            logger.error("Error handling 'chat.user_data' event: %s", e)
            # Handle event handling error

    async def chat_message(self, event):
        """
        Handles the 'chat.message' event.
        """
        try:
            # Extract message data from the event
            message = event["message"]
            action = event["action"]

            logger.info("Sending message to client: %s", message)

            # Send the message to the client
            await self.send(
                text_data=json.dumps(
                    {"type": "chat.message", "action": action, "message": message}
                )
            )
        except Exception as e:
            logger.error("Error handling 'chat.message' event: %s", e)
            # Handle event handling error

    @database_sync_to_async
    def is_user_authorized(self):
        # Get the user associated with the WebSocket connection
        user = self.scope["user"]

        # Check if the user is enrolled in the course
        is_enrolled = Enrollment.is_student_enrolled(user, self.course)
        print("is_enrolled: ", is_enrolled)

        # Check if the user is the teacher of the course
        is_teacher = self.course.teacher == user
        print("is_teacher: ", is_teacher)

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
            room = ChatRoom.objects.get(chat_name=self.room_name)
            return room.course
        except ChatRoom.DoesNotExist:
            return None
        
    @database_sync_to_async
    def get_last_viewed_message(self, chat_room_id):
            # Retrieve or create the ChatMembership object for the given user and chat room
            chat_membership, created = ChatMembership.objects.get_or_create( user_id=self.scope['user'].id, chat_room_id=chat_room_id)
            
            if chat_membership.last_viewed_message_id is not None:
                logger.info("last_viewed_message_id: %d", chat_membership.last_viewed_message_id)
            else:
                logger.info("last_viewed_message_id: None")
                
            # Return the last_viewed_message
            return chat_membership.last_viewed_message_id
        

    @database_sync_to_async
    def updateLastViewedMessageId(self, chat_room_id, message_id):
        try:
            logger.info("Updating the last viewed message id for %s.", self.scope['user'].username)
            # Retrieve the ChatMembership object for the given user and chat room
            chat_membership, created = ChatMembership.objects.get_or_create(user_id=self.scope['user'].id, chat_room_id=chat_room_id)

            # Update the last_viewed_message field with the message_id
            chat_membership.last_viewed_message_id = message_id  # Assuming last_viewed_message_id is the actual field name
            chat_membership.save()
            logger.info("Saved data to the database for %s", self.scope['user'].username)

            # Optionally, return True to indicate success
            return True
        except Exception as e:
            # Handle the exception
            logger.error("Error updating last viewed message id for %s: %s", self.scope['user'].username, str(e))
            return False


    def get_connected_users(self):
        """
        Retrieves list of connected users.

        Returns:
            list: List of connected users.
        """
        users = []
        for username, room_group_name in self.connected_users.items():
            if self.room_group_name in room_group_name:
                users.append(username)
        return users

    async def send_user_data(self, users):
        """
        Sends user data to the room group.

        Args:
            users (list): List of connected users.
        """
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.user_data", 
                    "action": "user_connected", 
                    "users": users
                    },
            )
            logger.info("User data sent successfully to room group")
        except Exception as e:
            logger.error("Failed to send user data: %s", e)
            # Handle send failure
            
    
    async def process_message_data(self, message_data):
        """
        Process incoming message data by adding user ID, retrieving related chat room and user instances,
        serializing the message data, validating it, and saving the validated message object to the database.

        Args:
            message_data (dict): The incoming message data containing chat room, user, and message details.

        Returns:
            dict: The cleaned and saved message object data.

        Raises:
            ValueError: If the message data is invalid.
        """
        try:
            # Log the full name of the user
            logger.info("Full name: %s", self.scope["user"].get_full_name())

            # Retrieve the IDs of the chat room and user from the message data
            chat_room_id = message_data["message"]["chat_room"]
            user_id = self.scope["user"].id

            # Create a dictionary containing the message data with IDs
            message_payload = {
                "chat_room": chat_room_id,
                "user": user_id,
                "content": message_data["message"].get("content", None),
                "file": message_data["message"].get("file", None),
                # Include any other fields as needed
            }

            # Now serialize the message data using the MessageSerializer
            message_serializer =  await database_sync_to_async(MessageSerializer)(data=message_payload)

            # Check if the serializer data is valid
            is_valid = await database_sync_to_async(message_serializer.is_valid)()

            if is_valid:
                # Save the validated message object to the database
                cleaned_message = await database_sync_to_async(message_serializer.save)()
                logger.info("Message data is valid. Message created with ID: %s", cleaned_message.id)
                return cleaned_message
            else:
                errors = await database_sync_to_async(message_serializer.errors.get)('chat_room')
                logger.error("Message data is invalid: %s", errors)
                raise ValueError("Invalid message data")

        except KeyError as e:
            logger.error("KeyError: %s", e)
            raise ValueError("Invalid message data")
        except ValidationError as e:
            logger.error("Validation error while saving message: %s", e)
            raise ValueError("Invalid message data")
        except Exception as e:
            logger.error("An error occurred while processing the message: %s", e)
            raise ValueError("Invalid message data")