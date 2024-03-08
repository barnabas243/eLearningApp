from django.test import Client
import pytest
from django.urls import reverse
from courses.models import Course
from courses.views import CoursesView
from users.tests.fixtures import teacher_user, official_course, draft_course


@pytest.mark.django_db
class TestCoursesView:
    @pytest.fixture(autouse=True)
    def setup(self, official_course, draft_course):
        self.official_course = official_course
        self.draft_course = draft_course

    def test_get_course_list(self):
        # Create a test client
        client = Client()

        # Get the URL for the courses view
        url = reverse("courses")

        # Make a GET request to the courses view
        response = client.get(url)

        # Check that the response status code is 200 (OK)
        assert response.status_code == 200

        # Check that the official course is in the response context
        assert self.official_course in response.context["courses"]

        # Check that the unofficial course is not in the response context
        assert self.draft_course not in response.context["courses"]


@pytest.mark.django_db
class TestCourseDetailsView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = Client()
        self.course = Course.objects.create(title="Test Course")
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

    def test_course_details_authenticated_enrolled(self):
        # Enroll the user in the course
        Enrolment.objects.create(user=self.user, course=self.course)

        # Login the user
        self.client.login(username="testuser", password="testpassword")

        # Make a GET request to the course details view
        response = self.client.get(
            reverse("course-details", kwargs={"course_id": self.course.id})
        )

        # Check that the response status code is 200 (OK)
        assert response.status_code == 200

        # Check that the correct course is in the response context
        assert response.context["course"] == self.course

        # Check that the user is enrolled in the course
        assert response.context["is_enrolled"] is True

    def test_course_details_authenticated_not_enrolled(self):
        # Login the user
        self.client.login(username="testuser", password="testpassword")

        # Make a GET request to the course details view
        response = self.client.get(
            reverse("course-details", kwargs={"course_id": self.course.id})
        )

        # Check that the response status code is 200 (OK)
        assert response.status_code == 200

        # Check that the correct course is in the response context
        assert response.context["course"] == self.course

        # Check that the user is not enrolled in the course
        assert response.context["is_enrolled"] is False
