# tests/test_decorators.py
from django.http import HttpResponse
import pytest
from courses.tests.factories import EnrolmentFactory
from users.tests.fixtures import teacher_user, request_factory, student_user


from courses.decorators import check_student_banned


@pytest.mark.django_db
class TestUserDecorators:
    @pytest.fixture(autouse=True)
    def setup(self, request_factory, student_user, teacher_user):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.request_factory = request_factory

    def test_check_student_banned_not_enrolled(self):
        request = self.request_factory.get("/")

        # Create a user with student role and a non-banned enrolment
        student = self.student_user
        request.user = student

        response = check_student_banned(lambda request: HttpResponse())(request)

        assert response.status_code == 403

    def test_check_student_not_banned(self):
        request = self.request_factory.get("/")

        # Create a user with student role and a non-banned enrolment
        student = self.student_user
        enrolment1 = EnrolmentFactory(student=student, is_banned=False)
        request.user = student

        response = check_student_banned(lambda request: HttpResponse())(request)

        assert response.status_code == 200

    def test_check_student_is_banned(self):
        request = self.request_factory.get("/")
        student = self.student_user

        # Create a user with student role and a banned enrolment
        enrolment2 = EnrolmentFactory(student=student, is_banned=True)
        request.user = student

        response = check_student_banned(lambda request: HttpResponse())(request)

        assert response.status_code == 403

    def test_check_student_is_not_student(self):
        request = self.request_factory.get("/")
        teacher = self.teacher_user

        request.user = teacher

        response = check_student_banned(lambda request: HttpResponse())(request)

        assert response.status_code == 403
