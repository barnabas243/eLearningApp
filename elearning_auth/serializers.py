from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
import logging

from users.models import User

logger = logging.getLogger(__name__)


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=User._meta.get_field("username").max_length
    )
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get("username", "").strip()
        password = attrs.get("password", "").strip()

        user = authenticate(username=username, password=password)

        if not user:
            logger.info("user: %s", user)
            raise serializers.ValidationError(
                detail="Invalid username or password.", code="invalid"
            )

        if not user.is_active:
            raise serializers.ValidationError(
                detail="User account is disabled.", code="inactive"
            )

        attrs["user"] = user
        return attrs


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)
    date_of_birth = serializers.DateField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def validate_password1(self, value):
        """
        Validate the password1 field against Django's password validators.
        """

        validate_password(value)
        return value

    def validate(self, data):
        """
        Custom validation to check if password1 and password2 match.
        """
        password1 = data.get("password1")
        password2 = data.get("password2")

        if password1 != password2:
            raise serializers.ValidationError("The passwords do not match.")

        return data

    def create(self, validated_data):
        # Remove password1 and password2 from validated data
        validated_data.pop("password2")

        validated_data["password"] = validated_data.pop("password1")

        return User.objects.create_user(
            **validated_data
        )  # automatically hashes password


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)
    confirm_password = serializers.CharField(max_length=128, write_only=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def validate_old_password(self, value):
        if not self.user:
            raise ValidationError("User not found.", code="user_not_found")
        if not check_password(value, self.user.password):
            raise ValidationError(
                "Incorrect old password.", code="invalid_old_password"
            )
        return value

    def validate(self, data):
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        validate_password(new_password)

        if new_password != confirm_password:
            raise ValidationError(
                "Passwords do not match.", code="new_password_mismatch"
            )

        # Check if the new password is the same as the old password
        if self.user and check_password(new_password, self.user.password):
            raise ValidationError(
                "New password cannot be the same as old password.",
                code="same_as_old_password",
            )

        return data

    def save(self):
        new_password = self.validated_data["new_password"]
        self.user.set_password(new_password)
        self.user.save(update_fields=["password"])
