import datetime
import pytest
from users.models import User
from users.serializers import (
    UserSerializer,
    UserUpdateSerializer,
)
from users.tests.fixtures import student_user


@pytest.mark.django_db
class TestUserSerializer:
    @pytest.fixture(autouse=True)
    def setup(self, student_user):
        self.student_user = student_user

    def test_user_serializer(self):
        serializer = UserSerializer(instance=self.student_user)
        expected_data = {
            "id": self.student_user.id,  # Corrected user ID
            "username": self.student_user.username,
            "first_name": self.student_user.first_name,
            "last_name": self.student_user.last_name,
            "email": self.student_user.email,
            "date_of_birth": str(
                self.student_user.date_of_birth
            ),  # Convert date to string
            "user_type": User.STUDENT,
        }
        assert serializer.data == expected_data

    def test_user_update_serializer(self):
        update_data = {
            "username": "tester123",
            "email": "tester123@example.com",
            "first_name": "Updated First Name",
            "last_name": "Updated Last Name",
            "date_of_birth": "2023-12-21",  # YYYY-MM-DD FORMAT. other formats will trigger invalid
        }
        serializer = UserUpdateSerializer(
            instance=self.student_user, data=update_data, partial=True
        )

        assert serializer.is_valid(), serializer.errors

        # Debugging: Print serializer.errors to view errors if invalid
        print(serializer.errors)

        updated_user = serializer.save()

        # Debugging: Print the updated user to verify changes
        print(updated_user.__dict__)

        assert updated_user.username == "tester123"
        assert updated_user.email == "tester123@example.com"
        assert updated_user.date_of_birth == datetime.date(2023, 12, 21)
        assert updated_user.first_name == "Updated First Name"
        assert updated_user.last_name == "Updated Last Name"
