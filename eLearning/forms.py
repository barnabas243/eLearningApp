from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from .models import User, Course, CourseMaterial  # Import your User model
from django.forms.widgets import DateInput
from datetime import date
from .tasks import process_image


class UserLoginForm(AuthenticationForm):
    """
    Form for user authentication.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["username", "password"]:
            self.fields[field_name].widget.attrs.update({"class": "form-control"})


class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration.
    """

    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="First name")
    last_name = forms.CharField(label="Last name")
    user_type = forms.ChoiceField(
        label="User type",
        choices=User.USER_TYPE_CHOICES,
        initial=User.STUDENT,
    )

    today = date.today()
    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=DateInput(attrs={"type": "date", "min": "1900-01-01", "max": today}),
    )

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + (
            "email",
            "first_name",
            "last_name",
            "user_type",
            "date_of_birth",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_order = [
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "date_of_birth",
            "password1",
            "password2",
        ]
        for field_name in field_order:
            self.fields[field_name].widget.attrs.update({"class": "form-control mb-3"})

    def save(self, commit=True):
        """
        Save the user instance.
        """

        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.user_type = self.cleaned_data["user_type"]
        user.date_of_birth = self.cleaned_data["date_of_birth"]
        if commit:
            user.save()
        return user


class UserPasswordChangeForm(PasswordChangeForm):
    """
    Form for password change.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["old_password", "new_password1", "new_password2"]:
            self.fields[field_name].widget.attrs.update({"class": "form-control"})


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["photo"]

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Call Celery task to process the image
        if instance.photo:
            process_image.delay(instance.photo.path)

        if commit:
            instance.save()

        return instance


class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "summary", "duration_weeks"]

        labels = {
            "name": "Course Name",
            "summary": "summary",
            "duration_weeks": "Duration (weeks)",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter course name"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter course summary",
                }
            ),
            "duration_weeks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter duration in weeks",
                }
            ),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "summary", "start_date", "description"]

        labels = {
            "name": "Course Name",
            "summary": "summary",
            "start_date": "Start Date",
            "description": "Description",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter course name"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter course summary",
                }
            ),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "description": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter course description",
                }
            ),
        }


class MaterialUploadForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = [
            "material",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields["material"].widget.attrs.update({"class": "form-control mb-3"})
