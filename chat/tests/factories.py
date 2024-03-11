from factory.django import DjangoModelFactory
from factory import SubFactory, Faker, LazyAttribute
from chat.models import ChatRoom, Message, ChatMembership
from courses.tests.factories import CourseFactory
from users.tests.factories import UserFactory
from django.utils.text import slugify


class ChatRoomFactory(DjangoModelFactory):
    class Meta:
        model = ChatRoom

    course = SubFactory(CourseFactory)
    chat_name = LazyAttribute(lambda _: slugify(Faker("word")))


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    chat_room = SubFactory(ChatRoomFactory)
    user = SubFactory(UserFactory)
    content = LazyAttribute(lambda _: Faker("text"))


class ChatMembershipFactory(DjangoModelFactory):
    class Meta:
        model = ChatMembership

    user = SubFactory(UserFactory)
    chat_room = SubFactory(ChatRoomFactory)
    last_viewed_message = SubFactory(MessageFactory)
    last_active_timestamp = LazyAttribute(lambda _: Faker("date_time_this_year"))
