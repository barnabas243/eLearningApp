# tests/test_decorators.py
from django.http import HttpResponse
from django.urls import reverse
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from elearning_auth.tests.fixtures import user, inactive_user
from users.tests.fixtures import request_factory


@pytest.mark.django_db
class TestUserDecorators:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.inactive_user = inactive_user
        self.client = APIClient()
        self.request_factory = request_factory

    def test_authenticated_user_access_on_home(self):
        # Log in the user
        self.client.force_login(user=self.user)

        # Make a GET request to the home view
        response = self.client.get(reverse("home"))

        # Check if the response status code is 200 (OK)
        assert response.status_code == 200

    def test_unauthenticated_user_access_on_home(self):

        # Make a GET request to the home view
        response = self.client.get(reverse("home"))

        # Check if the response status code is 200 (OK)
        assert response.status_code == 302

        # check that next query pointing to home
        assert response.url == reverse("login") + "?next=/home/"
