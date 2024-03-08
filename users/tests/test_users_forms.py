import pytest
from users.forms import ProfilePictureForm, StatusUpdateForm
from users.tests.factories import StatusUpdateFactory

from users.tests.fixtures import mock_photo, status_updates, student_user, teacher_user
import io
from PIL import Image


@pytest.mark.django_db
class TestUserForms:
    @pytest.fixture(autouse=True)
    def setup(self, student_user, mock_photo, teacher_user, status_updates):
        self.student_user = student_user
        self.teacher_user = teacher_user
        self.status_updates = status_updates
        self.mock_photo = mock_photo

    def test_profile_picture_form(self):
        post_data = {}
        file_data = {"photo": self.mock_photo}

        # Create form instance with POST and FILES data
        form = ProfilePictureForm(post_data, file_data, instance=self.student_user)

        # Assert form is valid
        assert form.is_valid(), form.errors

        # Save form
        form.save()

        # retrieve the updated student photo
        with open(self.student_user.photo.path, "rb") as f:
            uploaded_photo_bytes = f.read()

        # Open the mock photo as an image
        with Image.open(self.mock_photo) as mock_photo_image:
            # Convert the image to bytes
            with io.BytesIO() as mock_photo_bytes_io:
                mock_photo_image.save(mock_photo_bytes_io, format="JPEG")
                mock_photo_bytes = mock_photo_bytes_io.getvalue()

        # Compare the binary content of the images
        assert uploaded_photo_bytes == mock_photo_bytes

    def test_status_update_form(self):
        # Prepare form data
        status_data = {
            "content": "Test status update content",
        }
        student_update = StatusUpdateFactory.create(user=self.student_user)

        form = StatusUpdateForm(data=status_data, instance=student_update)

        # Assert form is valid
        assert form.is_valid(), form.errors

        # Save the form
        status_update = form.save()

        # Assert status update is saved with correct content and user
        assert status_update.content == "Test status update content"
        assert status_update.user == self.student_user
        assert status_update.created_at is not None

    def test_empty_status_update_form(self):
        # Prepare form data with an empty content field
        status_data = {
            "content": "",
        }

        # Create a status update instance
        student_update = StatusUpdateFactory.create(user=self.student_user)

        # Create form instance with invalid form data
        form = StatusUpdateForm(data=status_data, instance=student_update)

        # Assert form is invalid
        assert not form.is_valid()

        assert "content" in form.errors
        assert form.errors["content"] == ["This field is required."]

        # Check if the status update object remains unchanged
        assert student_update.content != ""

    def test_overflow_status_update_form(self):
        # Create a string that exceeds the maximum length (1000 characters)
        long_content = "a" * 1001

        # Prepare form data with content that exceeds the maximum length
        status_data = {
            "content": long_content,
        }

        # Create a status update instance
        student_update = StatusUpdateFactory.create(user=self.student_user)

        # Create form instance with invalid form data
        form = StatusUpdateForm(data=status_data, instance=student_update)

        # Assert form is invalid
        assert not form.is_valid()
        print(form.errors)

        # Check if the content field has a validation error
        assert "content" in form.errors
        assert form.errors["content"] == [
            "Ensure this value has at most 1000 characters (it has 1001)."
        ]

        # Assert that the form is not saved when it contains invalid data
        with pytest.raises(ValueError):
            form.save()

        # Check if the status update object remains unchanged
        assert student_update.content != "a" * 1001
