import pytest
from users.tests.factories import UserFactory


@pytest.fixture
def user():
    return UserFactory(password="ThisMustBeAn3xtremelyComplexed")


@pytest.fixture
def inactive_user():
    return UserFactory(password="ThisMustBeAn3xtremelyComplexed", is_active=False)


@pytest.fixture
def valid_user_payload():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "user_type": "student",
        "date_of_birth": "2000-01-01",
        "password1": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
        "password2": "ThisMustBeAn3xtremelyComplexedPAsswordForDJango",
    }
