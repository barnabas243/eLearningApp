import pytest

from chat.tests.factories import ChatRoomFactory


@pytest.fixture
def chatRoom(official_course):
    return ChatRoomFactory(course=official_course, chat_name="chat-name-test")
