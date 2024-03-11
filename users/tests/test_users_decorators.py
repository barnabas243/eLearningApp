# tests/test_decorators.py
from django.http import HttpResponse
import pytest
from courses.tests.factories import EnrolmentFactory
from users.decorators import teacher_required, student_required
from users.tests.fixtures import teacher_user, request_factory, student_user


@pytest.mark.django_db
class TestUserDecorators:
    @pytest.fixture(autouse=True)
    def setup(self, request_factory, student_user, teacher_user):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.request_factory = request_factory

    def test_teacher_required(self):
        request = self.request_factory.get("/")

        # Create a user with teacher role
        teacher = self.teacher_user
        request.user = teacher
        # Call the view function wrapped by the decorator
        response = teacher_required(lambda request: HttpResponse())(request)

        # Assert that the response status code is 200 since the user is a teacher
        assert response.status_code == 200

    def test_student_denied_teacher_required(self):
        request = self.request_factory.get("/")

        # student should return error 403
        student = self.student_user
        request.user = student
        response = teacher_required(lambda request: HttpResponse())(request)

        # Assert that the response status code is 403 since the user is a student
        assert response.status_code == 403

    def test_student_required(self):
        request = self.request_factory.get("/")

        student = self.student_user
        request.user = student

        response = student_required(lambda request: HttpResponse())(request)

        # Assert that the response status code is 200 since the user is a teacher
        assert response.status_code == 200

    def test_teacher_denied_student_required(self):
        request = self.request_factory.get("/")

        print("Teacher groups:")
        for group in self.teacher_user.groups.all():
            print(group.name)

        print("Student groups:")
        for group in self.student_user.groups.all():
            print(group.name)

        teacher = self.teacher_user
        request.user = teacher

        response = student_required(lambda request: HttpResponse())(request)

        assert response.status_code == 403
