from django.contrib.auth.models import User

from rest_framework.test import APIClient
from django.urls import reverse
import pytest
from chat.tests.factories import ChatRoomFactory
from chat.views import get_chat_rooms_for_user, room
from courses.tests.fixtures import (
    enrol,
    enrolled_student_user,
    official_course,
    teacher_user,
)
from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser

from users.tests.fixtures import request_factory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages


@pytest.mark.django_db
def test_index_view(enrol, enrolled_student_user, official_course, teacher_user):
    client = APIClient()
    user = enrolled_student_user
    client.force_login(user)

    # Make a GET request to the index view
    response = client.get(
        reverse("chat")
    )  # Update the URL as per your URL configuration

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200

    rendered_content = response.content.decode("utf-8")
    # Check if the correct template is used
    assert "chat/private/index.html" in [
        template.name for template in response.templates
    ]

    chat_rooms = get_chat_rooms_for_user(user)
    assert (
        render_to_string(
            "chat/partials/chat_room_list.html",
            {"chat_rooms": chat_rooms},
        )
        in rendered_content
    )


@pytest.mark.django_db
class TestRoomView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        enrol,
        enrolled_student_user,
        official_course,
        teacher_user,
        request_factory,
        chatRoom,
    ):
        self.enrol = enrol
        self.enrolled_student_user = enrolled_student_user
        self.official_course = official_course
        self.teacher_user = teacher_user
        self.request_factory = request_factory
        self.chatRoom = chatRoom

    def test_room_view_authenticated(self):
        # Create a user
        user = self.enrolled_student_user

        # Create a request
        factory = self.request_factory
        request = factory.get(
            reverse("room", kwargs={"room_name": self.chatRoom.chat_name})
        )
        request.user = user

        # Call the view function
        response = room(request, room_name=self.chatRoom.chat_name)

        # Assert that the response status code is 200
        assert response.status_code == 200

    def test_room_view_unauthenticated(self):
        # Create a chat room

        # Create a request
        factory = self.request_factory
        request = factory.get(
            reverse("room", kwargs={"room_name": self.chatRoom.chat_name})
        )
        request.user = AnonymousUser()
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))
        # Call the view function
        response = room(request, room_name=self.chatRoom.chat_name)

        # Assert that the response is a redirect
        assert response.status_code == 302  # Redirect status code

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "You need to log in to access this page." in str(messages[0])
