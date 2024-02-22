from rest_framework import serializers
from .models import ChatRoom, Message, ChatMembership
from eLearning.serializers import CourseSerializer, UserSerializer
import logging

logger = logging.getLogger(__name__)

class ChatRoomSerializer(serializers.ModelSerializer):
    course = CourseSerializer()  # Assuming you have a CourseSerializer

    class Meta:
        model = ChatRoom
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        
    def create(self, validated_data):
        # Retrieve the validated chat_room and user data
        chat_room_instance = validated_data.pop('chat_room')
        user_instance = validated_data.pop('user')

        
        # Get the IDs directly from the model instances
        chat_room_id = chat_room_instance.id
        user_id = user_instance.id
        logger.info("validated chat_room_id %d and validated user_id %d", chat_room_id, user_id) 
        
        # Create the Message instance with the extracted IDs and other validated data
        message = Message.objects.create(chat_room_id=chat_room_id, user_id=user_id, **validated_data)
        return message

class ChatMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Assuming you have a UserSerializer
    chatroom = ChatRoomSerializer()  # Assuming you have a ChatRoomSerializer
    last_viewed_message = MessageSerializer()  # Assuming you have a MessageSerializer

    class Meta:
        model = ChatMembership
        fields = '__all__'