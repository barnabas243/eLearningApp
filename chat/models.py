from django.db import models
from eLearning.models import Course, User
from django.utils import timezone


class ChatRoom(models.Model):
    """
    Model to represent a chat room associated with a course.
    """

    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name="chat_room",
        help_text="The course associated with this chat room.",
    )
    chat_name = models.CharField(max_length=255, help_text="The name of the chat room.")

    class Meta:
        unique_together = ("course", "chat_name")

    def save(self, *args, **kwargs):
        if not self.chat_name:
            self.chat_name = self.course.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chat Room for {self.course}"


def message_file_path(instance, filename):
    """
    Function to define the file path for message file uploads.
    """
    return f"message_files/{instance.chat_room.course.id}/{instance.user.id}/{filename}"


class Message(models.Model):
    """
    Model to represent a message in a chat room.
    """

    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        help_text="The chat room this message belongs to.",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user who sent the message."
    )
    content = models.TextField(
        max_length=2048,
        blank=True,
        null=True,
        help_text="The text content of the message.",
    )
    file = models.FileField(
        upload_to=message_file_path,
        blank=True,
        null=True,
        help_text="Optional file attachment.",
    )

    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="The timestamp when the message was created."
    )

    def __str__(self):
        return f"Message from {self.user} in {self.chat_room} at {self.timestamp}"


class ChatMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    last_viewed_message = models.ForeignKey(
        Message, on_delete=models.CASCADE, null=True, blank=True
    )
    last_online_timestamp = models.DateTimeField(
        default=timezone.now, help_text="The timestamp when the user disconnects"
    )
