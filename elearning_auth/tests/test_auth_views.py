# elearning_auth/tests/test_auth_views.py
from django.urls import reverse
import pytest
from rest_framework.test import APIClient
from users.tests.fixtures import request_factory, student_user

from elearning_auth.views import logout_user


@pytest.mark.django_db
def test_logout_user(student_user):
    client = APIClient()

    client.force_authenticate(user=student_user)

    # Make a GET request to the logout view
    response = client.get(reverse("logout"))

    # Check if the user is redirected to the login page after logout
    assert response.status_code == 302
    assert response.url == reverse("login")

    # Check if the user is logged out
    assert "_auth_user_id" not in client.session
