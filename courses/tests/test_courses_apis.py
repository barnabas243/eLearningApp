import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from notifications.models import Notification

from courses.tests.fixtures import enrolled_student_user


@pytest.mark.django_db
class TestNotificationView:
    @pytest.fixture(autouse=True)
    def setup(self, enrolled_student_user):
        self.enrolled_student_user = enrolled_student_user
        self.client = APIClient()

    def test_mark_notification_as_read(self):
        # Create a notification
        notification = Notification.objects.create(
            recipient=self.enrolled_student_user, unread=True
        )

        # Authenticate the user
        self.client.force_authenticate(user=self.enrolled_student_user)

        # Make a PATCH request to mark the notification as read
        response = self.client.patch(
            f"/api/notifications/{notification.id}/mark_as_read/"
        )

        # Check if the response status is 204 (No Content)
        assert response.status_code == 204

        # Refresh the notification from the database
        notification.refresh_from_db()

        # Check if the notification is marked as read
        assert not notification.unread

    def test_mark_nonexistent_notification_as_read(self):
        # Authenticate the user
        self.client.force_authenticate(user=self.enrolled_student_user)

        # Make a PATCH request to mark a nonexistent notification as read
        response = self.client.patch("/api/notifications/9999/mark_as_read/")

        # Check if the response status is 404 (Not Found)
        assert response.status_code == 404
