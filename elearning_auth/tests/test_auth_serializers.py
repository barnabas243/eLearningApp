import pytest
from elearning_auth.serializers import (
    PasswordChangeSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)
from rest_framework import serializers
from elearning_auth.tests.fixtures import inactive_user, user, valid_user_payload
from users.models import User
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import check_password


@pytest.mark.django_db
class TestLoginSerializer:
    @pytest.fixture(autouse=True)
    def setup(self, user, inactive_user):
        self.user = user
        self.inactive_user = inactive_user
        self.loginSerializer = UserLoginSerializer()

    def test_valid_authenticate(self):
        # Create a valid login payload
        valid_payload = {
            "username": self.user.username,
            "password": "ThisMustBeAn3xtremelyComplexed",
        }

        # Validate the payload using the serializer
        validated_data = self.loginSerializer.validate(valid_payload)

        # Assert that the validated data contains the user
        assert "user" in validated_data
        assert validated_data["user"] == self.user

    def test_invalid_authenticate(self):
        # Create an invalid login payload with wrong password
        invalid_payload = {"username": self.user.username, "password": "wrongpassword"}

        # Check if the serializer raises a validation error for invalid login
        with pytest.raises(serializers.ValidationError) as exc_info:
            self.loginSerializer.validate(invalid_payload)

        # Assert the validation error details
        assert exc_info.value.detail[0] == "Invalid username or password."

    def test_inactive_user_authenticate(self):
        # Deactivate the user
        # Create a login payload for the inactive user
        inactive_user_payload = {
            "username": self.inactive_user.username,
            "password": "ThisMustBeAn3xtremelyComplexed",
        }

        # Check if the serializer raises a validation error for inactive user
        with pytest.raises(serializers.ValidationError) as exc_info:
            self.loginSerializer.validate(inactive_user_payload)

        # Assert the validation error details
        assert exc_info.value.detail[0] == "User account is disabled."


@pytest.mark.django_db
class TestRegisterSerializer:
    @pytest.fixture(autouse=True)
    def setup(self, user, valid_user_payload):
        self.user = user
        self.valid_payload = valid_user_payload
        self.registrationSerializer = UserRegistrationSerializer()

    def test_valid_registration(self):

        # Validate the payload using the serializer
        serializer = UserRegistrationSerializer(data=self.valid_payload)

        assert serializer.is_valid(), serializer.errors

        # print(serializer.errors)

        registered_user = serializer.save()

        # Assert that the user is created successfully
        assert registered_user is not None
        assert isinstance(registered_user, User)

    def test_email_already_exists(self):
        # Test registration with an invalid email
        invalid_payload = self.valid_payload

        invalid_payload["email"] = self.user.email
        serializer = UserRegistrationSerializer(data=invalid_payload)

        assert not serializer.is_valid(), serializer.errors

        # Debugging: Print serializer.errors to view errors if invalid
        print("serializer errors: ", serializer.errors)

        assert "email" in serializer.errors

        error = serializer.errors["email"][0]  # Access the first element of the list
        assert error == "Email is already registered."

    def test_email_invalid_format(self):
        # Test registration with an invalid email
        invalid_payload = self.valid_payload

        invalid_payload["email"] = "test_example@"
        serializer = UserRegistrationSerializer(data=invalid_payload)

        assert not serializer.is_valid(), serializer.errors

        print("serializer errors: ", serializer.errors)

        assert "email" in serializer.errors

        error = serializer.errors["email"][0]
        assert error == "Enter a valid email address."

    def test_existing_username(self):
        # Test registration with an existing email
        invalid_payload = self.valid_payload

        invalid_payload["username"] = self.user.username
        serializer = UserRegistrationSerializer(data=invalid_payload)

        assert not serializer.is_valid(), serializer.errors

        # Debugging: Print serializer.errors to view errors if invalid
        print(serializer.errors)

        assert "username" in serializer.errors
        error = serializer.errors["username"][0]

        assert error == "Username is already taken."

    def test_password_too_common(self):
        # Test registration with an existing email
        invalid_payload = self.valid_payload

        invalid_payload["password1"] = "password123"
        invalid_payload["password2"] = "password123"

        serializer = UserRegistrationSerializer(data=invalid_payload)

        assert not serializer.is_valid(), serializer.errors

        # Debugging: Print serializer.errors to view errors if invalid
        print(serializer.errors)

        assert "password1" in serializer.errors

        password1_error = serializer.errors["password1"][0]

        assert password1_error == "This password is too common."

    def test_passwords_not_match(self):
        # Test registration with an existing email
        invalid_payload = self.valid_payload
        invalid_payload["password2"] = "password12344444444"

        serializer = UserRegistrationSerializer(data=invalid_payload)

        assert not serializer.is_valid(), serializer.errors

        # Debugging: Print serializer.errors to view errors if invalid
        print(serializer.errors)

        assert "non_field_errors" in serializer.errors

        error = serializer.errors["non_field_errors"][0]

        assert error == "The passwords do not match."


@pytest.mark.django_db
class TestPasswordChangeSerializer:
    @pytest.fixture(autouse=True)
    def setup(self, user, valid_user_payload):
        self.user = user
        self.valid_payload = valid_user_payload
        self.passwordChangeSerializer = PasswordChangeSerializer(user=user)

    def test_valid_password_change(self):
        # Create a valid password change payload
        valid_payload = {
            "old_password": "ThisMustBeAn3xtremelyComplexed",
            "new_password": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
            "confirm_password": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
        }
        # Validate the payload using the serializer
        validated_data = self.passwordChangeSerializer.validate(valid_payload)

        # Assert that the validated data contains the correct values
        assert (
            validated_data["new_password"]
            == "ThisMustBeAn3xtremelyComplexedPAsswordForDJango"
        )
        assert (
            validated_data["confirm_password"]
            == "ThisMustBeAn3xtremelyComplexedPAsswordForDJango"
        )

    def test_invalid_old_password(self):
        # Create an invalid password change payload with incorrect old password
        invalid_payload = {
            "old_password": "wrongpassword",
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        }

        # Check if the serializer raises a validation error for incorrect old password
        with pytest.raises(ValidationError) as exc_info:
            self.passwordChangeSerializer.validate_old_password(
                invalid_payload["old_password"]
            )

        # Assert the validation error details
        assert exc_info.value.detail[0] == "Incorrect old password."

    def test_password_mismatch(self):
        # Create an invalid password change payload with mismatched passwords
        invalid_payload = {
            "old_password": "ThisMustBeAn3xtremelyComplexed",
            "new_password": "ThisMustBeAn3xtremely",
            "confirm_password": "newpassword2",
        }

        # Check if the serializer raises a validation error for password mismatch
        with pytest.raises(ValidationError) as exc_info:
            self.passwordChangeSerializer.validate(invalid_payload)

        # Assert the validation error details
        assert exc_info.value.detail[0] == "Passwords do not match."

    def test_same_as_old_password(self):
        # Create an invalid password change payload with new password same as old password
        invalid_payload = {
            "old_password": "ThisMustBeAn3xtremelyComplexed",
            "new_password": "ThisMustBeAn3xtremelyComplexed",
            "confirm_password": "ThisMustBeAn3xtremelyComplexed",
        }

        # Check if the serializer raises a validation error for same new and old passwords
        with pytest.raises(ValidationError) as exc_info:
            self.passwordChangeSerializer.validate(invalid_payload)

        # Assert the validation error details
        assert (
            exc_info.value.detail[0]
            == "New password cannot be the same as old password."
        )
