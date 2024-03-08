import pytest
import io
from PIL import Image
from factory import LazyAttribute
from factory.faker import Faker
from django.utils.text import slugify
from django.test import RequestFactory
from chat.tests.factories import ChatMembershipFactory, ChatRoomFactory, MessageFactory
from courses.models import Course
from courses.tests.factories import (
    CourseFactory,
    EnrolmentFactory,
)
from users.models import User
from users.tests.factories import UserFactory, StatusUpdateFactory
from django.core.files.uploadedfile import SimpleUploadedFile


## ===============================================
## User general mock data
## ===============================================


@pytest.fixture
def student_user():
    return UserFactory(user_type=User.STUDENT)


@pytest.fixture
def teacher_user():
    return UserFactory(user_type=User.TEACHER)


@pytest.fixture
def status_updates(request, student_user, teacher_user):
    used_fixture_name = request.fixturename
    if used_fixture_name == "student_user":
        return StatusUpdateFactory.create_batch(5, user=student_user)
    elif used_fixture_name == "teacher_user":
        return StatusUpdateFactory.create_batch(5, user=teacher_user)


@pytest.fixture
def mock_photo():
    # Create a new blank image with PIL
    image = Image.new("RGB", (100, 100), color="white")

    # Convert the image to bytes
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG")

    # Return the SimpleUploadedFile with the image bytes
    return SimpleUploadedFile(
        "test_photo.jpg", image_bytes.getvalue(), content_type="image/jpeg"
    )


@pytest.fixture
def official_course(teacher_user):
    return CourseFactory(teacher=teacher_user, status=Course.OFFICIAL)


@pytest.fixture
def draft_course(teacher_user):
    return CourseFactory(teacher=teacher_user)


@pytest.fixture
def enrolment(student_user, official_course):
    return EnrolmentFactory(student=student_user, course=official_course)


@pytest.fixture
def chat_room(official_course):
    return ChatRoomFactory(
        course=official_course,
        chat_name=LazyAttribute(lambda o: slugify(o.course.name)),
    )


@pytest.fixture
def message(request, chat_room, student_user, teacher_user):
    used_fixture_name = request.fixturename
    if used_fixture_name in ("student_user", "teacher_user"):
        current_user = (
            student_user if used_fixture_name == "student_user" else teacher_user
        )
        return MessageFactory(
            chat_room=chat_room, user=current_user, content=Faker("text")
        )


@pytest.fixture
def chat_membership(request, chat_room, student_user, teacher_user):
    used_fixture_name = request.fixturename
    if used_fixture_name in ("student_user", "teacher_user"):
        current_user = (
            student_user if used_fixture_name == "student_user" else teacher_user
        )
        return ChatMembershipFactory(user=current_user, chat_room=chat_room)


@pytest.fixture
def request_factory():
    return RequestFactory()
