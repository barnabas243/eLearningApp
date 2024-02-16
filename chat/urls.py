from django.urls import path
from chat import views
from chat.apis import ChatRoomView


urlpatterns = [
    path("", views.index, name="index"),
    path("<str:room_name>/", views.room, name="room"),
]