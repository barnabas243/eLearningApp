from django.contrib import admin
from .models import ChatRoom, Message

# Register the ChatRoom model with the Django admin
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'course')
    list_filter = ('course',)
    search_fields = ('name', 'course__name')
    ordering = ('id',)

# Register the Message model with the Django admin
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_room', 'user', 'timestamp')
    list_filter = ('chat_room__course',)
    search_fields = ('content', 'user__username', 'chat_room__name')
    ordering = ('-timestamp',)
