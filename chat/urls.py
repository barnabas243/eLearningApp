from django.urls import path
from chat import views


urlpatterns = [
    path("", views.index, name="chat"),
    path("<str:room_name>/", views.room, name="room"),
    path("search/users/<int:chat_room_id>", views.search_users, name="search_users"),
]
