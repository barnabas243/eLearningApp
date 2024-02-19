from django.db import models
from eLearning.models import Course, User
from django.core.validators import URLValidator


class ChatRoom(models.Model):
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='chat_room',  # Add related_name for easier reverse lookup
        help_text='The course associated with this chat room.'
    )
    name = models.CharField(max_length=255, help_text='The name of the chat room.')

    class Meta:
        unique_together = ('course', 'name')
        
    def __str__(self):
        return f"Chat Room for {self.course}"


def message_file_path(instance, filename):
    # Define the file path within the media directory
    return f"message_files/{instance.chat_room.course.id}/{instance.user.id}/{filename}"

class Message(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',  # Add related_name for easier reverse lookup
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    content = models.TextField()
    
    file = models.FileField(upload_to=message_file_path, blank=True, null=True, help_text='Optional file attachment.')
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Message from {self.user} in {self.chat_room} at {self.timestamp}"
