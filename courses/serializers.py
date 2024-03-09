from rest_framework import serializers, validators
from django.utils.translation import gettext_lazy as _
from courses.models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseMaterial,
    Enrolment,
    Feedback,
)

from users.serializers import UserSerializer
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Course.objects.all(),
                fields=("name", "teacher"),
                message=_("The course name and teacher should be unique together."),
            )
        ]


class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = "__all__"


class MaterialUploadSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    week_number = serializers.IntegerField()
    material = serializers.ListField(child=serializers.FileField())


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = "__all__"


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"


class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = Enrolment
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
