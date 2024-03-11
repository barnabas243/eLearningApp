from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
)
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from faker import Faker
import pytest
from django.urls import reverse
from chat.models import ChatRoom
from courses.models import (
    AssignmentSubmission,
    Course,
    CourseMaterial,
    Enrolment,
    Feedback,
)
from courses.tests.fixtures import (
    assignmentMaterial,
    courseMaterials,
    enrol,
    enrolled_student_user,
    not_enrolled_student_user,
    official_course_1_week,
    teacher_user,
    official_course,
    draft_course,
)
from courses.views import (
    OfficialCourseView,
    WeekView,
    create_course,
    delete_course_material,
    get_week_materials,
    getCourseDateRange,
    publish_course,
    student_ban_status_update,
    submit_feedback,
    upload_assignment_material,
    upload_material,
    upload_student_submission,
)
from elearning_auth.tests.fixtures import user
from rest_framework.test import APIClient

from users.tests.fixtures import mock_photo, request_factory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages

DEFAULT_PASSWORD = "ThisMustBeAn3xtremelyComplexed"


@pytest.mark.django_db
class TestCoursesView:
    @pytest.fixture(autouse=True)
    def setup(self, official_course, draft_course):
        self.official_course = official_course
        self.draft_course = draft_course

    def test_get_course_list(self):
        # Create a test client
        client = APIClient()

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
    def setup(
        self,
        enrolled_student_user,
        not_enrolled_student_user,
        enrol,
        official_course,
    ):
        self.client = APIClient()
        self.enrolled_user = enrolled_student_user
        self.not_enrolled_user = not_enrolled_student_user
        self.official_course = official_course
        self.enrol = enrol
        self.courseDetailsURL = reverse(
            "course_details", kwargs={"course_id": self.official_course.id}
        )

    def test_course_details_authenticated_enrolled(self):
        self.client.force_login(self.enrolled_user)

        # Make a GET request to the course details view
        response = self.client.get(self.courseDetailsURL)

        # Check that the response status code is 200 (OK)
        assert response.status_code == 200

        # Check that the correct course is in the response context
        assert response.context["course"] == self.official_course

        # Check that the user is enrolled in the course
        assert response.context["is_enrolled"] is True

    def test_course_details_authenticated_not_enrolled(self):
        # Login the user
        self.client.force_login(self.not_enrolled_user)

        # Make a GET request to the course details view
        response = self.client.get(self.courseDetailsURL)

        # Check that the response status code is 200 (OK)
        assert response.status_code == 200

        # Check that the correct course is in the response context
        assert response.context["course"] == self.official_course

        # Check that the user is not enrolled in the course
        assert response.context["is_enrolled"] is False


@pytest.mark.django_db
class TestEnrollView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        enrolled_student_user,
        not_enrolled_student_user,
        enrol,
        official_course,
    ):
        self.client = APIClient()
        self.enrolled_user = enrolled_student_user
        self.not_enrolled_user = not_enrolled_student_user
        self.official_course = official_course
        self.enrol = enrol
        self.enrollURL = reverse(
            "enroll", kwargs={"course_id": self.official_course.id}
        )

    def test_enroll_user_not_enrolled(self):
        # Login the user
        self.client.force_login(self.not_enrolled_user)

        # Make a POST request to the enroll view
        response = self.client.post(self.enrollURL)

        # Check that the response status code is 201 (Created)
        assert response.status_code == 201

        # Check that the enrollment was created
        assert Enrolment.objects.filter(
            student=self.not_enrolled_user, course=self.official_course
        ).exists()

        # Check that the enrollment email was sent (not tested here)

    def test_enroll_user_already_enrolled(self):

        self.client.force_login(self.enrolled_user)

        # Make a POST request to the enroll view
        response = self.client.post(self.enrollURL)

        # Check that the response status code is 400 (Bad Request)
        assert response.status_code == 400

        # Check that the enrollment was not created again
        assert (
            Enrolment.objects.filter(
                student=self.enrolled_user, course=self.official_course
            ).count()
            == 1
        )
        # Check that the error message is returned in the response
        assert response.json() == {
            "message": "You are already enrolled in this course."
        }


@pytest.mark.django_db
class TestCreateCourseView:
    @pytest.fixture(autouse=True)
    def setup(self, teacher_user, request_factory):
        self.factory = request_factory
        self.teacher_user = teacher_user

    def test_create_course_success(self):
        # Prepare form data
        form_data = {
            "name": "Test Course",
            "summary": "This is a default test course description",
            "duration_weeks": 20,  # default
            # Add other required form fields here
        }

        # Create a request with logged-in user
        request = self.factory.post(reverse("create_course"), data=form_data)
        request.user = self.teacher_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Call your view function with the request
        response = create_course(request)

        # Check the response
        assert response.status_code == 302  # Adjust this according to your logic
        assert response.url == reverse("draft", args=[1])

        # Check if the course is created successfully
        assert Course.objects.count() == 1
        assert Course.objects.first().name == "Test Course"

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Course created successfully." in str(messages[0])

    def test_create_course_failure(self):
        # Simulate invalid form data
        form_data = {}

        # Create a request
        request = self.factory.post(reverse("create_course"), data=form_data)
        request.user = self.teacher_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Call your view function with the request
        response = create_course(request)

        # Check that the user is redirected back to the home
        assert response.status_code == 302  # Redirect status code
        assert response.url == reverse("home")

        # Check if the appropriate error message is displayed

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "Failed to create course. Please check the form." in str(messages[0])

    def test_create_course_name_already_exist(self, official_course):
        # Simulate invalid form data
        form_data = {
            "name": official_course.name,
            "summary": "This is a default test course description",
            "duration_weeks": 20,  # default
            # Add other required form fields here
        }

        # Create a request
        request = self.factory.post(reverse("create_course"), data=form_data)
        request.user = self.teacher_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Call your view function with the request
        response = create_course(request)

        # Check that the user is redirected back to the home
        assert response.status_code == 302  # Redirect status code
        assert response.url == reverse("home")

        # Check if the appropriate error message is displayed

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "Course with the same name already exists." in str(messages[0])


@pytest.mark.django_db
class TestWeekView:
    @pytest.fixture(autouse=True)
    def setup(self, teacher_user, official_course, official_course_1_week):
        self.client = APIClient()
        self.client.force_login(teacher_user)
        self.official_course = official_course
        self.official_course_1_week = official_course_1_week

    def test_patch_week_success(self):
        # Ensure the initial value of duration_weeks
        initial_duration_weeks = self.official_course.duration_weeks

        response = self.client.patch(
            reverse("week", kwargs={"course_id": self.official_course.id})
        )

        assert response.status_code == 200

        # Refresh the course object from the database
        self.official_course.refresh_from_db()

        assert self.official_course.duration_weeks == initial_duration_weeks + 1

    def test_delete_week_success(self):
        initial_duration_weeks = self.official_course.duration_weeks

        response = self.client.delete(
            reverse("week", kwargs={"course_id": self.official_course.id})
        )

        assert response.status_code == 200

        # Refresh the course object from the database
        self.official_course.refresh_from_db()

        assert self.official_course.duration_weeks == initial_duration_weeks - 1

    def test_delete_week_invalid(self):
        initial_duration_weeks = self.official_course_1_week.duration_weeks

        response = self.client.delete(
            reverse("week", kwargs={"course_id": self.official_course_1_week.id})
        )

        assert response.status_code == 400

        # Refresh the course object from the database
        self.official_course_1_week.refresh_from_db()

        assert self.official_course_1_week.duration_weeks == initial_duration_weeks


@pytest.mark.django_db
class TestOfficialCourseView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        teacher_user,
        request_factory,
        not_enrolled_student_user,
        enrolled_student_user,
        official_course,
        enrol,
    ):
        self.factory = request_factory
        self.teacher_user = teacher_user
        self.not_enrolled_student_user = not_enrolled_student_user
        self.enrolled_student_user = enrolled_student_user
        self.enrol = enrol
        self.official_course = official_course
        self.officialURL = reverse(
            "official", kwargs={"course_id": self.official_course.id}
        )

    def test_teacher_access_course_page(self):
        request = self.factory.get(self.officialURL)
        request.user = self.teacher_user

        response = OfficialCourseView.as_view()(
            request, course_id=self.official_course.id
        )

        assert response.status_code == 200
        assert "course" in response.context_data
        assert response.context_data["course"] == self.official_course

    def test_student_access_course_page(self):

        request = self.factory.get(self.officialURL)
        request.user = self.enrolled_student_user

        response = OfficialCourseView.as_view()(
            request, course_id=self.official_course.id
        )

        assert response.status_code == 200
        assert "course" in response.context_data
        assert response.context_data["course"] == self.official_course

    def test_non_enrolled_user_access_course_page(self):
        request = self.factory.get(self.officialURL)
        request.user = self.not_enrolled_student_user

        with pytest.raises(PermissionDenied):
            OfficialCourseView.as_view()(request, course_id=self.official_course.id)

    def test_teacher_update_course_details_success(self):
        request = self.factory.post(
            self.officialURL,
            data={
                "name": "New Course Name",  # Update with valid data
                "summary": self.official_course.summary,
                "description": self.official_course.description,
                "start_date": self.official_course.start_date,
            },
        )
        request.user = self.teacher_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = OfficialCourseView.as_view()(
            request, course_id=self.official_course.id
        )

        # Check that the user is redirected back to the course
        assert response.status_code == 302
        assert response.url == reverse(
            "draft", kwargs={"course_id": self.official_course.id}
        )

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Course details updated successfully." in str(messages[0])

        # Refresh the course object from the database
        self.official_course.refresh_from_db()
        assert self.official_course.name == "New Course Name"

    def test_teacher_update_course_details_failure(self):
        initial_course_name = self.official_course.name

        request = self.factory.post(
            self.officialURL,
            data={
                "name": "",  # invalid name
                "summary": self.official_course.summary,
                "description": self.official_course.description,
                "start_date": self.official_course.start_date,
            },
        )
        request.user = self.teacher_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = OfficialCourseView.as_view()(
            request, course_id=self.official_course.id
        )

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == reverse(
            "draft", kwargs={"course_id": self.official_course.id}
        )

        # Refresh the course object from the database
        self.official_course.refresh_from_db()

        # Course name should remain unchanged
        assert self.official_course.name == initial_course_name

        # Check if error message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "name: This field is required." in str(messages[0])


@pytest.mark.django_db
class TestSubmitFeedbackView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        teacher_user,
        request_factory,
        not_enrolled_student_user,
        enrolled_student_user,
        official_course,
        enrol,
    ):
        self.factory = request_factory
        self.teacher_user = teacher_user
        self.not_enrolled_student_user = not_enrolled_student_user
        self.enrolled_student_user = enrolled_student_user
        self.enrol = enrol
        self.official_course_id = official_course.id
        self.submitFeedbackURL = (
            reverse(
                "submit_feedback",
                kwargs={
                    "course_id": self.official_course_id,
                },
            ),
        )

    def test_submit_feedback_valid(self):
        request = self.factory.post(
            self.submitFeedbackURL,
            data={
                "course_rating": 5,
                "teacher_rating": 4,
                "comments": "Great course!",
            },
        )
        request.user = self.enrolled_student_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = submit_feedback(request, self.official_course_id)

        assert response.status_code == 302

        assert response.url == reverse(
            "official", kwargs={"course_id": self.official_course_id}
        )

        # Check if the feedback object is created
        assert Feedback.objects.filter(
            course_id=self.official_course_id, user_id=self.enrolled_student_user.id
        ).exists()

        assert (
            Feedback.objects.filter(
                course_id=self.official_course_id, user_id=self.enrolled_student_user.id
            ).count()
            == 1
        )

        # Check if error message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Submitted a feedback successfully." in str(messages[0])

    def test_submit_feedback_invalid_rating(self):
        request = self.factory.post(
            self.submitFeedbackURL,
            data={
                "course_rating": 212,
                "teacher_rating": 4,
                "comments": "Great course!",
            },
        )
        request.user = self.enrolled_student_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = submit_feedback(request, self.official_course_id)

        assert response.status_code == 302

        assert response.url == reverse(
            "official", kwargs={"course_id": self.official_course_id}
        )

        # Check if error message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert (
            "Invalid form data. course_rating: Ensure this value is less than or equal to 5."
            in str(messages[0])
        )

    def test_submit_feedback_invalid_string(self):
        request = self.factory.post(
            self.submitFeedbackURL,
            data={
                "course_rating": "this will fail",
                "teacher_rating": 4,
                "comments": "Great course!",
            },
        )
        request.user = self.enrolled_student_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = submit_feedback(request, self.official_course_id)

        assert response.status_code == 302

        assert response.url == reverse(
            "official", kwargs={"course_id": self.official_course_id}
        )

        # Check if error message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "Invalid data format. Please provide integer ratings." in str(
            messages[0]
        )

    def test_submit_feedback_invalid_course_id(self):
        request = self.factory.post(
            self.submitFeedbackURL,
            data={
                "course_rating": 4,
                "teacher_rating": 4,
                "comments": "Great course!",
            },
        )
        request.user = self.enrolled_student_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = submit_feedback(request, 100)

        assert response.status_code == 302

        assert response.url == reverse("home")

        # Check if error message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "Course doesn't exist." in str(messages[0])


@pytest.mark.django_db
class TestGetWeekMaterialsView:
    @pytest.fixture(autouse=True)
    def setUp(
        self,
        request_factory,
        enrolled_student_user,
        official_course,
        courseMaterials,
        assignmentMaterial,
    ):
        self.factory = request_factory
        self.enrolled_student_user = enrolled_student_user
        self.official_course = official_course
        self.week_number = 1
        self.getWeekMaterials = reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.official_course.id,
                "week_number": self.week_number,
            },
        )
        self.course_materials = courseMaterials
        self.assignment = assignmentMaterial

    def test_get_week_materials(self):
        request = self.factory.get(self.getWeekMaterials)

        request.user = self.enrolled_student_user
        response = get_week_materials(
            request, self.official_course.id, self.week_number
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestUploadAssignmentMaterialView:
    @pytest.fixture(autouse=True)
    def setUp(self, request_factory, official_course, teacher_user):
        self.factory = request_factory
        self.official_course = official_course
        self.teacher_user = teacher_user
        self.week_number = 1
        self.uploadAssignmentmaterialURL = reverse(
            "upload_assignment_material",
            kwargs={
                "course_id": self.official_course.id,
                "week_number": self.week_number,
            },
        )

    def test_upload_assignment_material_success(self):
        valid_data = {
            "course_id": self.official_course.id,
            "week_number": self.week_number,
            "name": "new assignment",
            "instructions": "this is a richtextfield. html can be safely inserted",
            "duration_days": 40,
        }

        request = self.factory.post(
            self.uploadAssignmentmaterialURL,
            data=valid_data,
        )

        request.user = self.teacher_user
        request.session = {}
        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = upload_assignment_material(
            request, self.official_course.id, self.week_number
        )

        print(response.content.decode("utf-8"))
        assert response.status_code == 302

        assert response.url == reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.official_course.id,
                "week_number": self.week_number,
            },
        )

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Assignment material uploaded successfully." in str(messages[0])

    def test_upload_assignment_material_invalid_duration(self):
        invalid_data = {
            "course_id": self.official_course.id,
            "week_number": self.week_number,
            "name": "new assignment",
            "instructions": "this is a richtextfield. html can be safely inserted",
            "duration_days": 0,
        }

        request = self.factory.post(
            self.uploadAssignmentmaterialURL,
            data=invalid_data,
        )

        request.user = self.teacher_user
        request.session = {}
        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = upload_assignment_material(
            request, self.official_course.id, self.week_number
        )

        print(response.content.decode("utf-8"))
        assert response.status_code == 302

        assert response.url == reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.official_course.id,
                "week_number": self.week_number,
            },
        )

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "duration_days: Ensure this value is greater than or equal to 1." in str(
            messages[0]
        )


def create_mock_pdf_content():
    fake = Faker()
    pdf_content = fake.binary(
        length=1024
    )  # Generate binary content (adjust length as needed)
    return pdf_content


def create_pdf_file():
    pdf_content = create_mock_pdf_content()
    pdf_file = ContentFile(pdf_content, name="mock_pdf.pdf")
    return pdf_file


@pytest.mark.django_db
class TestUploadStudentSubmission:
    @pytest.fixture(autouse=True)
    def setUp(
        self,
        request_factory,
        enrolled_student_user,
        enrol,
        official_course,
        assignmentMaterial,
    ):
        self.factory = request_factory
        self.enrolled_student_user = enrolled_student_user
        self.enrol = enrol
        self.official_course = official_course
        self.assignment = assignmentMaterial
        self.uploadStudentAssignmentURL = reverse(
            "upload_student_submission",
            kwargs={
                "course_id": self.official_course.id,
                "assignment_id": self.assignment.id,
            },
        )

    def test_upload_student_submission_valid(self):
        mock_pdf = create_pdf_file()
        form_data = {"assignment_file": mock_pdf}

        request = self.factory.post(
            self.uploadStudentAssignmentURL,
            data=form_data,
        )

        request.user = self.enrolled_student_user

        request.session = {}
        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = upload_student_submission(
            request, self.official_course.id, self.assignment.id
        )

        print(response.content.decode("utf-8"))
        assert response.status_code == 302

        assert response.url == reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.assignment.course.id,
                "week_number": self.assignment.week_number,
            },
        )

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Assignment submitted successfully." in str(messages[0])

        # Check if the assignment submission is created
        assert AssignmentSubmission.objects.filter(
            assignment=self.assignment, student=self.enrolled_student_user
        ).exists

    def test_upload_student_submission_invalid_filetype(self, mock_photo):
        form_data = {"assignment_file": mock_photo}

        request = self.factory.post(
            self.uploadStudentAssignmentURL,
            data=form_data,
        )

        request.user = self.enrolled_student_user

        request.session = {}
        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = upload_student_submission(
            request, self.official_course.id, self.assignment.id
        )

        print(response.content.decode("utf-8"))
        assert response.status_code == 302

        assert response.url == reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.assignment.course.id,
                "week_number": self.assignment.week_number,
            },
        )

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "assignment_file" in str(messages[0])
        assert (
            "File extension “jpg” is not allowed. Allowed extensions are: pdf."
            in str(messages[0])
        )

        # Check if the assignment submission is created
        assert AssignmentSubmission.objects.filter(
            assignment=self.assignment, student=self.enrolled_student_user
        ).exists

    def test_upload_student_submission_invalid_assignment_id(self, mock_photo):
        mock_pdf = create_pdf_file()
        form_data = {"assignment_file": mock_pdf}

        request = self.factory.post(
            reverse(
                "upload_student_submission",
                kwargs={"course_id": self.official_course.id, "assignment_id": 9999},
            ),
            data=form_data,
        )

        request.user = self.enrolled_student_user

        request.session = {}
        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = upload_student_submission(request, self.official_course.id, 9999)

        print(response.content.decode("utf-8"))
        assert response.status_code == 302

        assert response.url == reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.assignment.course.id,
                "week_number": self.assignment.week_number,
            },
        )

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert "Assignment does not exist." in str(messages[0])


@pytest.mark.django_db
class TestDeleteCourseMaterialView:
    @pytest.fixture(autouse=True)
    def setUp(self, request_factory, official_course, teacher_user, courseMaterials):
        self.request_factory = request_factory
        self.official_course = official_course
        self.teacher_user = teacher_user
        self.courseMaterial = courseMaterials[0]
        self.deleteCourseMaterialURL = reverse(
            "delete_course_material",
            kwargs={"course_material_id": self.courseMaterial.id},
        )

    def test_delete_course_material_success(self):
        request = self.request_factory.delete(self.deleteCourseMaterialURL)

        request.user = self.teacher_user
        request.session = {}
        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Make the request to the view function
        response = delete_course_material(
            request, course_material_id=self.courseMaterial.id
        )

        # Assert that the response is a redirect with status code 303
        assert isinstance(response, HttpResponse)
        assert response.status_code == 303

        # Assert that the material is deleted
        assert not CourseMaterial.objects.filter(id=self.courseMaterial.id).exists()

        # Assert that success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Material deleted successfully." in str(messages[0])

    def test_delete_course_material_not_exists(self):
        request = self.request_factory.delete(
            reverse("delete_course_material", kwargs={"course_material_id": 999})
        )
        request.user = self.teacher_user
        request.session = {}

        setattr(request, "_messages", FallbackStorage(request))

        # Make the request to the view function
        try:
            response = delete_course_material(request, course_material_id=999)
        except Http404 as e:
            assert str(e) == "No CourseMaterial matches the given query."

        assert response.headers["location"] == request.META.get("HTTP_REFERER", "/")
        # Assert that error message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert messages[0].message == "The material you want to delete does not exist"


@pytest.mark.django_db
class TestStudentBanStatusUpdateView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        enrolled_student_user,
        enrol,
        teacher_user,
        official_course,
        request_factory,
    ):
        # Create a user, course, and enrolment for testing
        self.teacher_user = teacher_user
        self.enrolled_student_user = enrolled_student_user
        self.official_course = official_course
        self.enrolment = enrol
        self.studentBanURL = reverse(
            "update-ban-status",
            kwargs={
                "course_id": self.official_course.id,
                "student_id": self.enrolled_student_user.id,
            },
        )

        self.request_factory = request_factory

    def test_student_ban_status_update_is_banned(self):
        request = self.request_factory.patch(self.studentBanURL)
        request.user = self.teacher_user

        response = student_ban_status_update(
            request,
            course_id=self.official_course.id,
            student_id=self.enrolled_student_user.id,
        )

        # Check if the response is an HTTP response
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200

        # Check if the enrolment status is updated
        updated_enrolment = Enrolment.objects.get(pk=self.enrolment.pk)
        assert updated_enrolment.is_banned == True

    def test_student_ban_status_update_unbanned(self):
        self.enrolment.is_banned = True
        self.enrolment.save()

        request = self.request_factory.patch(self.studentBanURL)
        request.user = self.teacher_user

        response = student_ban_status_update(
            request,
            course_id=self.official_course.id,
            student_id=self.enrolled_student_user.id,
        )
        print("self.enrolment: ", self.enrolment.is_banned)
        # Check if the response is an HTTP response
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200

        # Check if the enrolment status is updated
        updated_enrolment = Enrolment.objects.get(pk=self.enrolment.pk)
        assert updated_enrolment.is_banned == False


@pytest.mark.django_db
class TestUploadMaterialView:
    @pytest.fixture(autouse=True)
    def setup(self, request_factory, official_course, teacher_user):
        self.request_factory = request_factory
        self.teacher_user = teacher_user
        self.official_course = official_course
        self.week_number = 1
        self.uploadMaterialURL = reverse(
            "upload_material",
            kwargs={
                "course_id": self.official_course.id,
                "week_number": self.week_number,
            },
        )

    def test_upload_material_success(self, mock_photo):
        form_data = {
            "course_id": self.official_course.id,
            "week_number": self.week_number,
            "material": mock_photo,
        }

        request = self.request_factory.post(self.uploadMaterialURL, data=form_data)
        request.user = self.teacher_user
        request.session = {}

        setattr(request, "_messages", FallbackStorage(request))

        response = upload_material(
            request, course_id=self.official_course.id, week_number=self.week_number
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "get_week_materials",
            kwargs={
                "course_id": self.official_course.id,
                "week_number": self.week_number,
            },
        )

        # Assert success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert messages[0].message == "1 materials uploaded successfully."


@pytest.mark.django_db
class TestPublishCourseView:

    @pytest.fixture(autouse=True)
    def setup(self, request_factory, teacher_user, draft_course, official_course):
        self.request_factory = request_factory
        self.teacher_user = teacher_user
        self.draft_course = draft_course
        self.official_course = official_course
        self.publishCourseURL = reverse(
            "publish_course", kwargs={"course_id": self.draft_course.id}
        )

    def test_publish_course_success(self):
        request = self.request_factory.post(self.publishCourseURL)

        request.user = self.teacher_user

        request.session = {}

        setattr(request, "_messages", FallbackStorage(request))

        response = publish_course(
            request,
            course_id=self.draft_course.id,
        )

        assert response.status_code == 302
        # Assert success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert messages[0].message == "Course published successfully."

        assert ChatRoom.objects.filter(course=self.draft_course).exists

    def test_publish_course_already_published(self):
        request = self.request_factory.post(self.publishCourseURL)

        request.user = self.teacher_user

        request.session = {}

        setattr(request, "_messages", FallbackStorage(request))

        response = publish_course(
            request,
            course_id=self.official_course.id,
        )

        assert response.status_code == 302
        # Assert success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert messages[0].message == "Course is already published."

    def test_publish_course_missing_fields(self):
        self.draft_course.description = ""
        self.draft_course.save()

        request = self.request_factory.post(self.publishCourseURL)

        request.user = self.teacher_user

        request.session = {}

        setattr(request, "_messages", FallbackStorage(request))

        response = publish_course(
            request,
            course_id=self.draft_course.id,
        )

        assert response.status_code == 302
        # Assert success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "error"
        assert (
            messages[0].message
            == "Cannot publish course. All fields (name, summary, description, start_date) are required."
        )
