from django.contrib.auth import login
import logging
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from elearning_auth.forms import UserRegistrationForm
from elearning_auth.serializers import (
    PasswordChangeSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)
from django.shortcuts import redirect
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from .forms import UserLoginForm
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST"), name="post")
class LoginAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auth/public/login.html"

    def get_renderers(self):
        if self.request.method == "POST":
            return [JSONRenderer()]  # Use JSONRenderer for POST requests
        return super().get_renderers()

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        form = UserLoginForm()
        return Response({"form": form}, template_name=self.template_name)

    def post(self, request, *args, **kwargs):
        try:
            serializer = UserLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user"]
            login(request, user)

            return Response({"detail": "Login successful."}, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            logger.error("errors: %s", e)
            if "non_field_errors" in e.detail:
                logger.error("errors: %s", e)
                if "User account is disabled." in e.detail["non_field_errors"]:
                    error_detail = "User account is disabled."

                    return Response(
                        {"error": error_detail},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            error_detail = "Invalid username or password."
            return Response(
                {"error": error_detail},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error("An error occurred during login: %s", str(e))
            return Response(
                {"error": "An error occurred during login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST"), name="post")
class RegisterAPIView(APIView):
    """
    API view for user registration.
    """

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "auth/public/register.html"

    def get_renderers(self):
        if self.request.method == "POST":
            return [JSONRenderer()]  # Use JSONRenderer for POST requests
        return super().get_renderers()

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        form = UserRegistrationForm()
        return Response({"form": form}, template_name=self.template_name)

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


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST"), name="post")
class PasswordChangeAPIView(APIView):
    def post(self, request):
        logger.info("Received a POST request to change password.")
        try:
            user = request.user
            # Create a serializer instance with parsed data and current user
            serializer = PasswordChangeSerializer(data=request.data, user=user)

            if serializer.is_valid():
                serializer.save()

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
                else:
                    error_detail = value[0]
                    status_code = status.HTTP_400_BAD_REQUEST

            return Response({"error": error_detail}, status=status_code)

        except Exception as e:
            # Log the exception
            logger.error("An error occurred while changing password: %s", str(e))
            # Return a generic error response
            return Response(
                {"error": "An error occurred while changing password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
