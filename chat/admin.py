from django.contrib import admin
from chat.models import ChatMembership, ChatRoom, Message


# Register the ChatRoom model with the Django admin
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "chat_name", "course")
    list_filter = ("course",)
    search_fields = ("chat_name", "course__name")
    ordering = ("id",)


# Register the Message model with the Django admin
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat_room", "user", "timestamp")
    list_filter = ("chat_room__course",)
    search_fields = ("content", "user__username", "chat_room__chat_name")
    ordering = ("-timestamp",)


@admin.register(ChatMembership)
class ChatMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "chat_room", "last_viewed_message", "last_online_timestamp")
    list_filter = ("chat_room",)
    search_fields = ("user__username",)
