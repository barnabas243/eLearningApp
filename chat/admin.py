from django.contrib import admin
from .models import ChatRoom

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('course', 'name')
    search_fields = ('course__name', 'name')
    list_filter = ('course__name',)