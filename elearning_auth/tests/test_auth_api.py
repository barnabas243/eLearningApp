import pytest
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from rest_framework.test import APIClient
from elearning_auth.apis import LoginAPIView
from elearning_auth.forms import UserLoginForm
from users.models import User

from users.tests.factories import UserFactory
from users.tests.fixtures import request_factory
from elearning_auth.tests.fixtures import user, inactive_user, valid_user_payload
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import authenticate


@pytest.mark.django_db
class TestLoginRegistrationAPIs:
    @pytest.fixture(autouse=True)
    def setup(self, user, inactive_user, request_factory):
        self.user = user
        self.inactive_user = inactive_user
        self.request_factory = request_factory

    def test_login_form_rendered_for_unauthenticated_user(self):
        request = self.request_factory.get(reverse("login"))
        request.session = {}
        request.user = AnonymousUser()

        # Set up messages framework
        setattr(request, "_messages", FallbackStorage(request))

        # Create an instance of LoginAPIView
        login_view = LoginAPIView()

        # Call the get method with the request
        response = login_view.get(request)

        # Check if the response contains the login form
        assert response.status_code == 200
        assert "form" in response.data
        assert response.data["form"].fields.keys() == UserLoginForm().fields.keys()

    def test_get_authenticated_user_redirected_to_home(self):
        client = APIClient()

        # Log in the user
        client.force_authenticate(user=self.user)

        print(self.user)
        # Make a POST request to the login endpoint
        response = client.get(reverse("login"))

        # Check if the response is a redirect
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_successful_login(self):
        client = APIClient()

        # Prepare login credentials
        username = self.user.username
        password = "ThisMustBeAn3xtremelyComplexed"

        # Make a POST request to the login API view
        response = client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

        # Check if the response status code is correct
        assert response.status_code == 200

        # Check if the login was successful by attempting to authenticate the user
        assert response.data["detail"] == "Login successful."

    def test_invalid_password_login(self):
        client = APIClient()

        # Prepare login credentials
        username = self.user.username
        password = "password123444"

        # Make a POST request to the login API view
        response = client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

        # Check if the response status code is correct
        assert response.status_code == 401
        # Check if 'error' exist in the response data
        assert "error" in response.data

        # Check if 'error' contain the expected error message
        assert response.data["error"] == "Invalid username or password."

    def test_empty_username_password_login(self):
        client = APIClient()

        # Prepare login credentials
        username = ""
        password = ""

        # Make a POST request to the login API view
        response = client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

        # Check if the response status code is correct
        assert response.status_code == 401
        # Check if 'error' exist in the response data
        assert "error" in response.data

        # Check if 'error' contain the expected error message
        assert response.data["error"] == "Invalid username or password."

    def test_inactive_user_login(self):
        client = APIClient()

        # Prepare login credentials
        username = self.inactive_user.username
        password = "ThisMustBeAn3xtremelyComplexed"

        # Make a POST request to the login API view
        response = client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

        # Check if the response status code is correct
        assert response.status_code == 401
        # Check if 'error' exist in the response data
        assert "error" in response.data

        # Check if 'error' contain the expected error message
        assert response.data["error"] == "User account is disabled."


@pytest.mark.django_db
class TestRegisterAPIView:

    @pytest.fixture(autouse=True)
    def setup(self, user, valid_user_payload):
        self.user = user
        self.client = APIClient()
        self.valid_user_payload = valid_user_payload
        self.registerURL = reverse("register")

    def test_get_authenticated_user_redirect_to_home(self):
        # Log in the user
        self.client.force_authenticate(user=self.user)

        # Make a GET request to the register endpoint
        response = self.client.get(self.registerURL)

        # Check if the response is a redirect to the home
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_get_unauthenticated_user(self):
        # Make a GET request to the register endpoint
        response = self.client.get(self.registerURL)

        # Check if the response status code is 200 (OK)
        assert response.status_code == 200

    def test_post_valid_registration(self):

        # Make a POST request to the register endpoint
        response = self.client.post(self.registerURL, self.valid_user_payload)

        # Check if the response status code is 201 (Created)
        assert response.status_code == 201

        # Check if the user is created and logged in
        assert User.objects.filter(username="testuser").exists()
        assert authenticate(
            username="testuser",
            password="ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
        )
        assert "_auth_user_id" in response.client.session

    def test_post_invalid_registration(self):
        # Prepare invalid registration data (missing required fields)
        # no need to do more since this is just to test that the view returns error 400
        invalid_data = {
            "username": "",
            "email": "",
            "first_name": "",
            "last_name": "",
            "user_type": "",
            "date_of_birth": "",
            "password1": "",
            "password2": "",
        }

        # Make a POST request to the register endpoint
        response = self.client.post(self.registerURL, invalid_data)

        # Check if the response status code is 400 (Bad Request)
        assert response.status_code == 400

        # Check if the response contains errors
        assert "username" in response.data
        assert "email" in response.data
        assert "first_name" in response.data
        assert "last_name" in response.data
        assert "user_type" in response.data
        assert "date_of_birth" in response.data
        assert "password1" in response.data
        assert "password2" in response.data


@pytest.mark.django_db
class TestPasswordChangeAPIView:

    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.client = APIClient()
        self.changePassURL = reverse("change-password")

    def test_change_password_success(self):
        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Prepare valid password change data
        data = {
            "old_password": "ThisMustBeAn3xtremelyComplexed",
            "new_password": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
            "confirm_password": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
        }

        # Make a POST request to change password
        response = self.client.post(self.changePassURL, data)

        # Check if the response status code is 200 (OK)
        assert response.status_code == 200

        # Check if the password has been changed
        assert self.user.check_password(
            "ThisMustBeAn3xtremelyComplexedPAsswordForDJango"
        )

    def test_change_password_invalid_old_password(self):
        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Prepare invalid password change data (incorrect old password)
        data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        }

        # Make a POST request to change password
        response = self.client.post(self.changePassURL, data)

        # Check if the response status code is 422 (Unprocessable Entity)
        assert response.status_code == 422

        # Check if the error message is correct
        assert response.data["error"] == "Incorrect old password."

    def test_new_password_same_as_old_password(self):
        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Prepare valid password change data
        data = {
            "old_password": "ThisMustBeAn3xtremelyComplexed",
            "new_password": "ThisMustBeAn3xtremelyComplexed",
            "confirm_password": "ThisMustBeAn3xtremelyComplexed",
        }

        # Make a POST request to change password
        response = self.client.post(self.changePassURL, data)

        # Check if the response status code is 400
        assert response.status_code == 400
        assert (
            response.data["error"] == "New password cannot be the same as old password."
        )

    def test_change_password_new_password_mismatch(self):
        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Prepare invalid password change data (new password mismatch)
        data = {
            "old_password": "ThisMustBeAn3xtremelyComplexed",
            "new_password": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
            "confirm_password": "differentpassword",
        }

        # Make a POST request to change password
        response = self.client.post(self.changePassURL, data)

        # Check if the response status code is 400 (Bad Request)
        assert response.status_code == 400

        # Check if the error message is correct
        assert response.data["error"] == "Passwords do not match."
