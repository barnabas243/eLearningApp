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
        read_only_fields = ["id", "username", "email"]


class StatusUpdateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StatusUpdate
        fields = "__all__"
