from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from users.models import StatusUpdate, User
import logging

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "user_type",
        ]
        read_only_fields = ["id", "username", "email", "user_type"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "date_of_birth"]

    def __init__(self, *args, **kwargs):
        # Dynamically set the fields based on the data sent in the request
        fields = kwargs.pop("fields", None)
        if fields:
            self.Meta.fields = fields
        super().__init__(*args, **kwargs)
