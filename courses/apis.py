import logging
from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from courses.serializers import NotificationSerializer
from django.utils.decorators import method_decorator
from elearning_auth.decorators import custom_login_required
from django.shortcuts import get_object_or_404


logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(custom_login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(recipient=user, unread=True)

    @action(detail=True, methods=["patch"])
    def mark_as_read(self, request, notification_id=None):
        queryset = self.get_queryset()
        notification = get_object_or_404(queryset, pk=notification_id)
        notification.unread = False
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {"error": "Notification does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            logger.error(f"An error occurred while marking notification as read: {exc}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
