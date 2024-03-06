from django.contrib.auth import login
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from elearning_auth.serializers import (
    PasswordChangeSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)


logger = logging.getLogger(__name__)


class LoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                login(request, user)

                return Response(
                    {"detail": "Login successful."}, status=status.HTTP_200_OK
                )
            else:
                # Handle validation errors
                logger.error("serializer.errors: %s", serializer.errors)
                if "inactive" in serializer.errors:
                    error_detail = "User account is disabled."
                    status_code = status.HTTP_401_UNAUTHORIZED
                elif "required" in serializer.errors:
                    error_detail = "Username and password must be provided."
                    status_code = status.HTTP_400_BAD_REQUEST
                else:
                    error_detail = "Invalid username or password."
                    status_code = status.HTTP_401_UNAUTHORIZED

                return Response(
                    {"error": error_detail},
                    status=status_code,
                )
        except Exception as e:
            logger.error("An error occurred during login: %s", str(e))
            return Response(
                {"error": "An error occurred during login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterAPIView(APIView):
    """
    API view for user registration.
    """

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)  # Automatically login the user after registration
            return Response(
                {"detail": "User registered successfully."},
                status=status.HTTP_201_CREATED,
            )
        else:
            errors = serializer.errors
            logger.error("User registration failed: %s", errors)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeAPIView(APIView):
    def post(self, request):
        logger.info("Received a POST request to change password.")
        try:
            user = request.user
            # Create a serializer instance with parsed data and current user
            serializer = PasswordChangeSerializer(data=request.data, user=user)

            # Validate the serializer data
            if serializer.is_valid():
                # Save the validated data
                serializer.save()
                # Return success response
                return Response(
                    {"detail": "Password changed successfully."},
                    status=status.HTTP_200_OK,
                )

            # Handle validation errors
            errors = serializer.errors
            logger.error("errors: %s", errors)
            error_detail = None
            status_code = status.HTTP_400_BAD_REQUEST
            for key, value in errors.items():
                if key == "old_password" and value[0].code == "invalid_old_password":
                    error_detail = "Incorrect old password."
                    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                    break
                elif (
                    key == "non_field_errors"
                    and value[0].code == "same_as_old_password"
                ):
                    error_detail = "New password cannot be the same as old password."
                    status_code = status.HTTP_400_BAD_REQUEST
                    break
                elif (
                    key == "non_field_errors"
                    and value[0].code == "new_password_mismatch"
                ):
                    error_detail = "Passwords do not match."
                    status_code = status.HTTP_400_BAD_REQUEST
                    break

            if not error_detail:
                error_detail = "Validation error occurred."

            return Response({"error": error_detail}, status=status_code)

        except Exception as e:
            # Log the exception
            logger.error("An error occurred while changing password: %s", str(e))
            # Return a generic error response
            return Response(
                {"error": "An error occurred while changing password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordChangeAPIView(APIView):
    def post(self, request):
        logger.info("Received a POST request to change password.")
        try:
            user = request.user
            # Create a serializer instance with parsed data and current user
            serializer = PasswordChangeSerializer(data=request.data, user=user)

            # Validate the serializer data
            if serializer.is_valid():
                # Save the validated data
                serializer.save()
                # Return success response
                return Response(
                    {"detail": "Password changed successfully."},
                    status=status.HTTP_200_OK,
                )

            # Handle validation errors
            errors = serializer.errors
            logger.error("errors: %s", errors)
            error_detail = None
            status_code = status.HTTP_400_BAD_REQUEST
            for key, value in errors.items():
                if key == "old_password" and value[0].code == "invalid_old_password":
                    error_detail = "Incorrect old password."
                    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                    break
                elif (
                    key == "non_field_errors"
                    and value[0].code == "same_as_old_password"
                ):
                    error_detail = "New password cannot be the same as old password."
                    status_code = status.HTTP_400_BAD_REQUEST
                    break
                elif (
                    key == "non_field_errors"
                    and value[0].code == "new_password_mismatch"
                ):
                    error_detail = "Passwords do not match."
                    status_code = status.HTTP_400_BAD_REQUEST
                    break

            if not error_detail:
                error_detail = "Validation error occurred."

            return Response({"error": error_detail}, status=status_code)

        except Exception as e:
            # Log the exception
            logger.error("An error occurred while changing password: %s", str(e))
            # Return a generic error response
            return Response(
                {"error": "An error occurred while changing password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
