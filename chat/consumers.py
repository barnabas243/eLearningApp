from django.utils import timezone
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.serializers import MessageSerializer
from django.core.serializers import serialize
from .models import ChatMembership, ChatRoom
from courses.models import Enrolment
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for the chat functionality.

    This consumer manages WebSocket connections for the chat feature of the application.
    It performs authentication, authorization, and joins users to chat rooms.
    """

    connected_users = {}  # maintain the connected clients without group_channels.

    # ===============================================
    # Socket Connection Functions
    # ===============================================
    async def connect(self):
        """
        Called when a WebSocket connection is established.

        This method performs authentication, verifies the availability of the associated course,
        checks if the user is authorized to access the chat room, and joins the user to the appropriate chat room.

        :raises WebSocketClose:
            - If the user is not authenticated, the WebSocket connection is closed with error code 4003
              and the reason "Anonymous Users are not allowed".

            - If the associated course is not found for the chat room, the WebSocket connection is closed
              with error code 4004 and the reason "Course not found for room".

            - If the user is not authorized to access the chat room, the WebSocket connection is closed
              with error code 4001 and the reason "User not authorized".
        """
        logger.info("Reached the chatconsumer")

        # Extract the room name from the URL route parameters
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Ensure the user is authenticated
        if isinstance(self.scope["user"], AnonymousUser):
            logger.error("Anonymous Users are not allowed")
            await self.close(code=4003, reason="Anonymous Users are not allowed")
            return

        # Check if the associated course exists
        self.course = await self.get_course_for_room()
        if not self.course:
            logger.error("Course not found for room")
            await self.close(code=4004, reason="Course not found for room")
            return

        # Check if the user is authorized to access the chat room
        authorized = await self.is_user_authorized()
        if not authorized:
            logger.error("User not authorized")
            await self.close(code=4001, reason="User not authorized")
            return

        # Store the user's WebSocket connection details
        username = self.scope[
            "user"
        ].username  # Assuming user ID is used as a unique identifier
        if username not in self.connected_users:
            self.connected_users[username] = []
        self.connected_users[username].append(self.room_group_name)

        # Accept the WebSocket connection and join the room group
        await self.accept()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def is_user_authorized(self):
        """
        Checks if the user is authorized to access the chat room.

        This method checks whether the user associated with the WebSocket connection
        is authorized to access the chat room. A user is considered authorized if
        they are enrolled in the course associated with the chat room or if they are
        the teacher of the course.

        :return: True if the user is authorized, False otherwise.
        :rtype: bool
        """
        # Get the user associated with the WebSocket connection
        user = self.scope["user"]

        # Check if the user is enrolled in the course
        is_enrolled = Enrolment.is_student_enrolled(user, self.course)

        # Check if the user is the teacher of the course
        is_teacher = self.course.teacher == user

        # User is authorized if they are enrolled in the course or if they are the teacher
        return is_enrolled or is_teacher

    @database_sync_to_async
    def get_course_for_room(self):
        """
        Retrieves the course associated with the chat room.

        This method queries the database to find the course associated with the chat room.

        :return: The course associated with the chat room, or None if the room doesn't exist.
        :rtype: Course or None
        """
        try:
            # Example: Querying the Course model based on the room name
            room = ChatRoom.objects.get(chat_name=self.room_name)
            return room.course
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def get_last_viewed_message(self, chat_room_id):
        """
        Retrieves the ID of the last message viewed by the user in the specified chat room.

        :param chat_room_id: The ID of the chat room.
        :type chat_room_id: int

        :return: The ID of the last viewed message, or None if no message is viewed.
        :rtype: int or None
        """
        try:
            # Retrieve or create the ChatMembership object for the given user and chat room
            chat_membership, created = ChatMembership.objects.get_or_create(
                user_id=self.scope["user"].id, chat_room_id=chat_room_id
            )

            if chat_membership.last_viewed_message_id is not None:
                logger.info(
                    "last_viewed_message_id: %d", chat_membership.last_viewed_message_id
                )
            else:
                logger.info("last_viewed_message_id: None")

            # Return the last_viewed_message
            return chat_membership.last_viewed_message_id
        except Exception as e:
            logger.error("Error retrieving last viewed message: %s", e)
            return None

    def get_connected_users(self):
        """
        Retrieves the list of connected users.

        :return: A list of connected users.
        :rtype: list
        """
        connected_users = []
        for username, room_group_name in self.connected_users.items():
            if self.room_group_name in room_group_name:
                connected_users.append(username)
        return connected_users

    # def get_all_chat_members(self, chat_room_id):

    #     get_all_users = ChatMembership.objects.filter(chat_room_id=chat_room_id)
    #     if(get_all_users):
    #         return get_all_users

    #     return None

    # ===============================================
    # Socket Disconnection Functions
    # ===============================================
    async def disconnect(self, close_code):
        """
        Handles the disconnection of a WebSocket connection.

        This method is called when a WebSocket connection is closed, and it performs cleanup tasks
        such as notifying other users about the disconnection, removing the user from the list of connected users,
        and leaving the room group.

        :param close_code: The code indicating the reason for the disconnection.
        :type close_code: int

        :raises WebSocketClose: If any error occurs during the disconnection process.
        """
        try:
            # Log the disconnection reason code and reason text
            logger.info("Disconnecting WebSocket connection.")

            # Notify other users about the disconnection
            await self.notify_user_disconnected()

            # Remove the user from connected_users
            self.remove_user_from_connected_users()

            # Leave the room group
            await self.leave_room_group()

            logger.info("WebSocket connection disconnected successfully")
        except Exception as e:
            logger.error("Failed to disconnect WebSocket connection: %s", e)

    async def notify_user_disconnected(self):
        """
        Notifies other users in the chat room about the disconnection of the current user.

        This method sends a message to the chat room group indicating that a user has disconnected.
        The message includes information about the disconnected user.

        :raises WebSocketClose: If any error occurs while sending the disconnection message.
        """

        user_data = await database_sync_to_async(ChatMembership.objects.filter)(
            user_id=self.scope["user"].id, chat_room__chat_name=self.room_name
        )

        serialized_data = await database_sync_to_async(serialize)("json", user_data)

        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.user_data",
                    "action": "user_disconnected",
                    "users": serialized_data,
                },
            )
            logger.debug("User disconnected message sent successfully to room group")
        except Exception as e:
            logger.error("Failed to send user disconnected message: %s", e)

    def remove_user_from_connected_users(self):
        """
        Removes the disconnected user from the connected_users dictionary.

        This method removes the user from the dictionary tracking connected users.
        It removes all occurrences of the room group name associated with the disconnected user.

        :raises KeyError: If the disconnected user's username is not found in the connected_users dictionary.
        :raises ValueError: If an error occurs while removing the user from the connected_users dictionary.
        """
        try:
            username = self.scope["user"].username
            # Iterate over the list and remove all occurrences of self.room_group_name
            while self.room_group_name in self.connected_users[username]:
                self.connected_users[username].remove(self.room_group_name)
                logger.debug("User removed from self.connected_users")

        except KeyError as e:
            logger.error(
                "Failed to remove user from self.connected_users: User '%s' not found.",
                username,
            )
            raise KeyError(
                f"User '{username}' not found in connected_users dictionary."
            ) from e

        except ValueError as e:
            logger.error("Failed to remove user from self.connected_users: %s", e)
            raise ValueError(
                "Error occurred while removing user from connected_users dictionary."
            ) from e

    async def leave_room_group(self):
        """
        Removes the WebSocket connection from the chat room group.

        This method removes the WebSocket connection from the chat room group,
        allowing the user to leave the chat room.

        :raises WebSocketClose: If any error occurs while leaving the room group.
        """
        try:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            logger.debug("Left the room group successfully")
        except Exception as e:
            logger.error("Failed to leave the room group: %s", e)
            # Handle leave failure

    # ===============================================
    # Socket Messaging Functions
    # ===============================================
    async def receive(self, text_data):
        """
        Receives and processes incoming messages from the WebSocket connection.

        This method handles incoming messages received from the WebSocket connection.
        It parses the incoming message data, processes it accordingly, and takes appropriate actions
        based on the contents of the message.

        :param text_data: The message data received from the WebSocket connection.
        :type text_data: str

        :raises Exception: If an error occurs during message processing.
        """
        try:
            # Parse the incoming message data as a dictionary
            message_data = json.loads(text_data)
            logger.debug("Received message_data: %s", message_data)

            # Check if the message is a request to retrieve user data or to close user connection
            if "action" in message_data:
                if message_data["action"] == "get_user_data":
                    # Handle request to retrieve user data
                    await self.handle_get_user_data(message_data)
                elif message_data["action"] == "close_user_connection":
                    # Handle request to update the last viewed message
                    await self.handle_last_viewed_message(message_data)
            else:
                # Process the incoming message
                await self.process_incoming_message(message_data)

        except Exception as e:
            logger.error("Failed to process incoming message: %s", e)
            # Handle message processing failure

    async def process_incoming_message(self, message_data):
        """
        Processes the incoming message from the WebSocket connection.

        This method processes the incoming message, saves it to the database,
        and broadcasts it to the chat room group.

        :param message_data: The message data received from the WebSocket connection.
        :type message_data: dict

        :raises Exception: If an error occurs during message processing.
        """
        try:
            # Save the validated message object to the database within a transaction
            cleaned_message = await self.process_message_data(message_data)
            logger.info("Processing incoming message")

            # Retrieve username and full name
            username = await database_sync_to_async(
                lambda: cleaned_message.user.username
            )()
            full_name = await database_sync_to_async(
                cleaned_message.user.get_full_name
            )()

            # Log the cleaned message with user data
            logger.info(
                "Cleaned message: %s, Username: %s, Full Name: %s",
                cleaned_message.content,
                username,
                full_name,
            )

            # Prepare message to broadcast
            message = {
                "id": cleaned_message.id,
                "content": cleaned_message.content,
                "username": username,
                "full_name": full_name,
                "timestamp": cleaned_message.timestamp.isoformat(),
                # Add any other fields you want to send
            }

            # Send the message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat.message", "action": "send_message", "message": message},
            )
            logger.info("Message sent to room group: %s", self.room_group_name)

        except Exception as e:
            logger.error("Failed to process incoming message: %s", e)
            # Handle message processing failure

    async def process_message_data(self, message_data):
        """
        Process incoming message data by adding user ID, retrieving related chat room and user instances,
        serializing the message data, validating it, and saving the validated message object to the database.

        :param message_data: The incoming message data containing chat room, user, and message details.
        :type message_data: dict

        :return: The cleaned and saved message object data.
        :rtype: dict

        :raises ValueError: If the message data is invalid.
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
            message_serializer = await database_sync_to_async(MessageSerializer)(
                data=message_payload
            )

            # Check if the serializer data is valid
            is_valid = await database_sync_to_async(message_serializer.is_valid)()

            if is_valid:
                # Save the validated message object to the database
                cleaned_message = await database_sync_to_async(
                    message_serializer.save
                )()
                logger.info(
                    "Message data is valid. Message created with ID: %s",
                    cleaned_message.id,
                )
                return cleaned_message
            else:
                errors = await database_sync_to_async(message_serializer.errors.get)(
                    "chat_room"
                )
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

    async def chat_user_data(self, event):
        """
        Handles the 'chat.user_data' event.

        :param event: A dictionary containing event data, including user information and action.
        :type event: dict

        :raises KeyError: If essential keys are missing in the event data.
        :raises Exception: If an unexpected error occurs during event handling.
        """
        try:
            # Retrieve user data and action from the event
            users = event.get("users")
            action = event.get("action")

            logger.info("Sending user data to client: %s", users)

            # Construct the message data
            message_data = {"type": "chat.user_data", "action": action, "users": users}

            # Send the message data to the client
            await self.send(text_data=json.dumps(message_data))

        except KeyError as e:
            logger.error("KeyError while handling 'chat.user_data' event: %s", e)
            # Handle KeyError (missing key in event)
        except Exception as e:
            logger.error("Error handling 'chat.user_data' event: %s", e)
            # Handle other exceptions during event handling

    async def chat_message(self, event):
        """
        Handles the 'chat.message' event.

        :param event: A dictionary containing event data, including the message and action.
        :type event: dict

        :raises KeyError: If essential keys are missing in the event data.
        :raises Exception: If an unexpected error occurs during event handling.
        """
        try:
            # Extract message data and action from the event
            message = event.get("message")
            action = event.get("action")

            logger.info("Sending message to client: %s", message)

            # Construct the message data
            message_data = {
                "type": "chat.message",
                "action": action,
                "message": message,
            }

            # Send the message data to the client
            await self.send(text_data=json.dumps(message_data))

        except KeyError as e:
            logger.error("KeyError while handling 'chat.message' event: %s", e)
            # Handle KeyError (missing key in event)
        except Exception as e:
            logger.error("Error handling 'chat.message' event: %s", e)
            # Handle other exceptions during event handling

    async def send_user_data(self, users):
        """
        Sends user data to the room group.

        :param users: List of connected users.
        :type users: list

        :raises: Exception: If there is an error while sending user data to the room group.
        """
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat.user_data", "action": "user_connected", "users": users},
            )
            logger.info("User data sent successfully to room group")
        except Exception as e:
            logger.error("Failed to send user data: %s", e)
            # Handle send failure

    async def handle_get_user_data(self, message_data):
        """
        Handles the request to retrieve user data from the WebSocket connection.

        This method processes the request to retrieve user data and sends the user data
        to the chat room group.

        :param message_data: The message data received from the WebSocket connection.
        :type message_data: dict

        :raises Exception: If an error occurs during the retrieval or sending of user data.
        """
        try:
            logger.info("Received request to get user data")
            logger.info("Connected users: %s", self.connected_users)
            # Retrieve list of connected users
            users = self.get_connected_users()
            chat_room_id = message_data["chat_room_id"]

            # Retrieve the last viewed message
            last_viewed_message = await self.get_last_viewed_message(chat_room_id)
            logger.debug("Connected users: %s", users)

            # Send user data to room group
            await self.send_user_data(users)
            logger.info("Sending user last viewed message...")

            # Send the last viewed message to the user
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "chat.user_data",
                        "action": "user_last_viewed_message",
                        "last_viewed_message": last_viewed_message,
                    }
                )
            )
            logger.info("Sent user last viewed message...")

        except Exception as e:
            logger.error("Failed to handle request to get user data: %s", e)
            # Handle failure to retrieve or send user data

    async def handle_last_viewed_message(self, message_data):
        """
        Handles the request to updates the last viewed message ID before disconnecting.

        :param message_data: The message data received from the WebSocket connection.
        :type message_data: dict

        :raises Exception: If an error occurs during the processing of the close user connection request.
        """
        try:
            logger.info(
                "Received request to save last_viewed_message before closing %s connection to %s",
                self.scope["user"].username,
                self.room_group_name,
            )

            # Update the last viewed message ID
            logger.info("message_data: %s", message_data)
            logger.info("last_viewed_message: %s", message_data["last_viewed_message"])
            logger.info("chat_room_id: %s", message_data["chat_room_id"])
            await self.update_last_viewed_message_id(
                message_data["chat_room_id"], message_data["last_viewed_message"]
            )

            logger.info(
                "Completed request before closing %s connection to %s",
                self.scope["user"].username,
                self.room_group_name,
            )

        except Exception as e:
            logger.error("Failed to handle request to close user connection: %s", e)
            # Handle failure to process close user connection request

    @database_sync_to_async
    def update_last_viewed_message_id(self, chat_room_id, message_id):
        """
        Updates the last viewed message ID for the user in the specified chat room.

        :param chat_room_id: The ID of the chat room.
        :type chat_room_id: int
        :param message_id: The ID of the last viewed message.
        :type message_id: int

        :return: True if the update is successful, False otherwise.
        :rtype: bool
        """
        try:
            logger.info(
                "Updating the last viewed message ID for %s.",
                self.scope["user"].username,
            )

            # Retrieve the ChatMembership object for the given user and chat room
            chat_membership, created = ChatMembership.objects.get_or_create(
                user_id=self.scope["user"].id, chat_room_id=chat_room_id
            )

            logger.info("Retrieved ChatMembership instance: %s", chat_membership)

            # Update the last_viewed_message field with the message_id
            chat_membership.last_viewed_message_id = message_id
            chat_membership.last_online_timestamp = timezone.now()

            logger.info("ChatMembership instance before saving: %s", chat_membership)

            chat_membership.save()
            logger.info(
                "Saved data to the database for %s", self.scope["user"].username
            )

            # Return True to indicate success
            return True
        except Exception as e:
            # Handle the exception
            logger.error(
                "Error updating last viewed message ID for %s: %s",
                self.scope["user"].username,
                str(e),
            )
            return False
