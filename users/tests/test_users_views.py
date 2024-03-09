import json
import pytest
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from users.views import (
    AutocompleteView,
    DashboardView,
    LandingView,
    ProfileView,
    UploadPictureView,
    userSearchFilter,
)
from django.contrib.messages import get_messages
from users.tests.fixtures import (
    draft_course,
    mock_photo,
    official_course,
    request_factory,
    student_user,
    status_updates,
    chat_room,
    enrolment,
    teacher_user,
)
from django.contrib.auth.models import AnonymousUser


@pytest.mark.django_db
class TestDashboardView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        student_user,
        teacher_user,
        status_updates,
        chat_room,
        enrolment,
        request_factory,
        draft_course,
        official_course,
    ):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.status_updates = status_updates
        self.chat_room = chat_room
        self.enrolment = enrolment
        self.draft_course = draft_course
        self.official_course = official_course
        self.request_factory = request_factory

    def test_authenticated_user_redirected_to_dashboard(self):
        # Create an authenticated user

        request = self.request_factory.get(reverse("landing"))
        request.user = self.student_user

        response = LandingView.as_view()(request)

        # Assert that the response is a redirect to the dashboard page
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_unauthenticated_user_render_landing_page(self):
        request = self.request_factory.get(reverse("landing"))
        request.user = AnonymousUser()

        response = LandingView.as_view()(request)

        # Assert that the response renders the landing page template
        assert response.status_code == 200
        assert response.template_name == ["users/public/landing.html"]

    def test_student_dashboard(self):
        # Make a request to the dashboard view
        request = self.request_factory.get(reverse("dashboard"))
        request.user = self.student_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Get the response from the view
        response = DashboardView.as_view()(request)
        # Assertions
        assert response.status_code == 200
        rendered_content = response.content.decode("utf-8")

        # Check if the correct template is rendered with the correct context data
        assert (
            render_to_string(
                "users/partials/profile_section.html", {"user": self.student_user}
            )
            in rendered_content
        )

        assert (
            render_to_string(
                "users/partials/status_update.html",
                {"status_updates": self.status_updates},
            )
            in rendered_content
        )

        assert (
            render_to_string(
                "users/partials/registered_courses.html",
                {"registered_courses": [self.enrolment.course]},
            )
            in rendered_content
        )
        assert (
            render_to_string(
                "users/partials/course_chats.html",
                {"course_chats": [self.chat_room]},
            )
            in rendered_content
        )

    def test_teacher_dashboard(self):
        # Make a request to the dashboard view
        request = self.request_factory.get(reverse("dashboard"))
        request.user = self.teacher_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Get the response from the view
        response = DashboardView.as_view()(request)

        # Assertions
        assert response.status_code == 200
        rendered_content = response.content.decode("utf-8")

        # Check if the correct template is rendered with the correct context data
        assert (
            render_to_string(
                "users/partials/profile_section.html", {"user": self.teacher_user}
            )
            in rendered_content
        )

        assert (
            render_to_string(
                "users/partials/status_update.html",
                {"status_updates": self.status_updates},
            )
            in rendered_content
        )

        assert (
            render_to_string(
                "users/partials/draft_courses.html",
                {"draft_courses": [self.draft_course]},
            )
            in rendered_content
        )

        assert (
            render_to_string(
                "users/partials/official_courses.html",
                {"official_courses": [self.official_course]},
            )
            in rendered_content
        )

        # assert (
        #     render_to_string(
        #         "users/partials/course_chats.html",
        #         {"course_chats": [chat_room]},
        #     )
        #     in rendered_content
        # )

    def test_post_valid_request(self):
        # Make a POST request to the dashboard view with valid data
        request = self.request_factory.post(
            reverse("dashboard"), data={"content": "Test status update"}
        )
        request.user = self.student_user
        request.session = {}

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        response = DashboardView.as_view()(request)

        # Assertions
        assert response.status_code == 302  # Redirects after successful submission

        # Get messages from the request
        messages = list(get_messages(request))

        # Assertions for correct error message
        assert len(messages) == 1  # Ensure only one message is present
        assert messages[0].level == 25  # default error level
        assert str(messages[0]) == "Status update posted successfully."

    def test_post_empty_content_request(self):
        # Create a user
        invalid_data = {"content": ""}  # Empty content should be rejected
        request_invalid = self.request_factory.post(
            reverse("dashboard"), data=invalid_data
        )
        request_invalid.user = self.student_user
        request_invalid.session = {}
        setattr(request_invalid, "_messages", FallbackStorage(request_invalid))

        response_invalid = DashboardView.as_view()(request_invalid)

        assert response_invalid.status_code == 302

        # Get messages from the request
        messages = list(get_messages(request_invalid))

        # Assertions for correct error message
        assert len(messages) == 1  # Ensure only one message is present
        assert messages[0].level == 40  # default error level
        assert str(messages[0]) == "Invalid form data. Please check your input."


@pytest.mark.django_db
class TestUserSearchFilter:
    @pytest.fixture(autouse=True)
    def setup(self, student_user, teacher_user, request_factory):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.request_factory = request_factory

    def test_student_search_by_username(self):
        query = self.student_user.username
        filtered_users = userSearchFilter(self.student_user.id, "student", query)
        assert self.student_user in filtered_users

    def test_student_search_by_email(self):
        query = self.student_user.email
        filtered_users = userSearchFilter(self.student_user.id, "student", query)
        assert self.student_user in filtered_users

    def test_student_search_by_full_name(self):
        query = self.student_user.get_full_name()
        filtered_users = userSearchFilter(self.student_user.id, "student", query)
        assert self.student_user in filtered_users

    def test_teacher_search_by_username(self):
        query = self.teacher_user.username
        filtered_users = userSearchFilter(self.teacher_user.id, "teacher", query)
        assert self.teacher_user in filtered_users

    def test_teacher_search_by_email(self):
        query = self.teacher_user.email
        filtered_users = userSearchFilter(self.teacher_user.id, "teacher", query)
        assert self.teacher_user in filtered_users

    def test_teacher_search_by_full_name(self):
        query = self.teacher_user.get_full_name()
        filtered_users = userSearchFilter(self.teacher_user.id, "teacher", query)
        assert self.teacher_user in filtered_users

    def test_no_matching_results(self):
        # Search query doesn't match any users
        query = "/??/??/??"
        filtered_users = userSearchFilter(self.student_user.id, "student", query)
        assert len(filtered_users) == 0

    def test_student_not_search_teacher(self):
        # students cannot search for teacher
        query = self.teacher_user.username
        filtered_users = userSearchFilter(self.student_user.id, "student", query)
        assert self.teacher_user not in filtered_users
        assert len(filtered_users) == 0

    def test_teacher_can_search_student(self):
        # teacher can search for student
        query = self.student_user.username
        filtered_users = userSearchFilter(self.teacher_user.id, "teacher", query)
        assert self.student_user in filtered_users
        assert len(filtered_users) == 1


@pytest.mark.django_db
class TestAutocompleteView:
    @pytest.fixture(autouse=True)
    def setup(self, student_user, teacher_user, request_factory):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.request_factory = request_factory

    def test_get_autocomplete_options(self):
        # the autoCompleteView uses the UserSearchFilter values to generate the datalist

        request = self.request_factory.get(
            reverse("autocomplete"), {"q": self.student_user.username}
        )
        request.user = self.student_user

        # Call the view function
        response = AutocompleteView.as_view()(request)

        # Assertions
        assert response.status_code == 200

        rendered_content = response.content.decode("utf-8")
        # Add more assertions as needed for the response content

        assert (
            render_to_string(
                "users/partials/autocomplete_options.html",
                {"users": [self.student_user]},
            )
            in rendered_content
        )


@pytest.mark.django_db
class TestProfileView:
    @pytest.fixture(autouse=True)
    def setup(self, student_user, teacher_user, mock_photo, request_factory):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.mock_photo = mock_photo
        self.request_factory = request_factory

    def test_get_profile(self):
        # Create a request to get the profile
        request = self.request_factory.get(reverse("profile"))
        request.user = self.student_user

        # Call the view function
        response = ProfileView.as_view()(request)

        # Assertions
        assert response.status_code == 200
        assert "Content-Type" in response
        assert response["Content-Type"] == "text/html; charset=utf-8"

        # Add more assertions as needed for the response content

    def test_put_unique_username_profile(self):
        # Create a request to update the username with unique value
        unique_username = "testing1"
        update_data = {"username": unique_username}  # Add your update data here
        request = self.request_factory.put(
            reverse("profile"),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        request.user = self.student_user

        # Call the view function
        response = ProfileView.as_view()(request)

        # Assertions
        assert response.status_code == 200
        assert "Content-Type" in response
        assert response["Content-Type"] == "application/json"
        assert self.student_user.username == unique_username

        response_data = json.loads(response.content)
        serializer_success = response_data.get("success")
        assert serializer_success is not None

        print(serializer_success)
        # Assert the specific error message
        assert serializer_success == "Profile updated successfully"

    def test_put_duplicate_username_profile(self):
        # Return error 400 if username already exists
        old_username = self.student_user.username

        assert old_username != self.teacher_user.username

        update_data = {"username": self.teacher_user.username}
        request = self.request_factory.put(
            reverse("profile"),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        request.user = self.student_user

        response = ProfileView.as_view()(request)

        # Assertions
        assert response.status_code == 400
        assert "Content-Type" in response
        assert response["Content-Type"] == "application/json"

        response_data = json.loads(response.content)
        serializer_errors = response_data.get("username")

        print(serializer_errors)

        assert serializer_errors is not None
        assert serializer_errors == ["User with this Username already exists."]

    def test_put_unique_email_profile(self):
        # Create a request to update the user email with unique email
        unique_email = "test123@gmail.com"

        update_data = {"email": unique_email}  # Add your update data here
        request = self.request_factory.put(
            reverse("profile"),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        request.user = self.student_user

        # Call the view function
        response = ProfileView.as_view()(request)

        # Assertions
        assert response.status_code == 200
        assert "Content-Type" in response
        assert response["Content-Type"] == "application/json"

        response_data = json.loads(response.content)
        serializer_success = response_data.get("success")
        assert serializer_success is not None

        print(serializer_success)
        # Assert the specific error message
        assert serializer_success == "Profile updated successfully"

    def test_put_duplicate_email_profile(self):
        # Create a request to update the user email with unique email

        assert self.student_user.email != self.teacher_user.email

        duplicate_email = self.teacher_user.email

        update_data = {"email": duplicate_email}  # Add your update data here
        request = self.request_factory.put(
            reverse("profile"),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        request.user = self.student_user

        # Call the view function
        response = ProfileView.as_view()(request)

        # Assertions
        assert response.status_code == 400
        assert "Content-Type" in response
        assert response["Content-Type"] == "application/json"

        response_data = json.loads(response.content)
        serializer_errors = response_data.get("email")
        assert serializer_errors is not None

        print(serializer_errors)
        # Assert the specific error message
        assert serializer_errors == ["User with this Email address already exists."]

    def test_put_invalid_email_profile(self):
        # Create a request to update the user email with unique email
        invalid_email = "test@example"
        old_email = self.student_user.email

        assert old_email != self.teacher_user.email

        update_data = {"email": invalid_email}  # Add your update data here

        request = self.request_factory.put(
            reverse("profile"),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        request.user = self.teacher_user

        # Call the view function
        response = ProfileView.as_view()(request)

        # Assertions
        assert response.status_code == 400
        assert "Content-Type" in response
        assert response["Content-Type"] == "application/json"
        assert self.student_user.email == old_email

    def test_upload_picture_success(self):
        # Create a POST request with the photo data
        request = self.request_factory.post(reverse("upload_picture"))
        request.user = self.student_user  # Assuming you have a user object
        request.FILES["photo"] = self.mock_photo

        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = UploadPictureView.as_view()(request)

        # Assertions
        assert response.status_code == 302  # Redirect on success

        # Check if success message is present
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert messages[0].tags == "success"
        assert "Profile photo has been updated successfully" in str(messages[0])
