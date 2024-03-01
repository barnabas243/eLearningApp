from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from eLearning.models import (
    Assignment,
    AssignmentSubmission,
    StatusUpdate,
    User,
    Course,
    CourseMaterial,
    Feedback,
)
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
                attrs={"class": "form-control", "placeholder": "course name"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "course summary",
                }
            ),
            "duration_weeks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "duration in weeks",
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
                attrs={"class": "form-control", "placeholder": "course name"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "course summary",
                }
            ),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class MaterialUploadForm(forms.ModelForm):
    course_id = forms.IntegerField(widget=forms.HiddenInput)
    week_number = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields["material"].widget.attrs.update({"class": "form-control mb-3"})
        # Allow multiple file selection
        self.fields["material"].widget.attrs["multiple"] = True

    class Meta:
        model = CourseMaterial
        fields = ["material"]


class AssignmentForm(forms.ModelForm):
    course_id = forms.IntegerField(widget=forms.HiddenInput)
    week_number = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = Assignment
        fields = ["name", "duration_days", "instructions"]
        labels = {
            "name": "Name",
            "instructions": "Instructions",
            "duration_days": "Duration (days)",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "assignment name"}
            ),
            "duration_days": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "duration in days"}
            ),
        }


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ["assignment_file"]
        labels = {
            "assignment_file": "File submission",
        }
        widgets = {
            "assignment_file": forms.FileInput(
                attrs={
                    "class": "form-control mb-3",
                    "accept": ".pdf",
                    "placeholder": "Select PDF file to submit",
                }
            ),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["course_rating", "teacher_rating", "comments"]
        labels = {
            "course_rating": "Course Rating",
            "teacher_rating": "Teacher Rating",
            "comments": "Comments",
        }
        widgets = {
            "comments": forms.Textarea(
                attrs={"rows": 4}
            ),  # Adjust the number of rows as needed
            "course_rating": forms.CheckboxSelectMultiple(
                choices=[(i, i) for i in range(1, 6)]
            ),
            "teacher_rating": forms.CheckboxSelectMultiple(
                choices=[(i, "") for i in range(1, 6)]
            ),
        }


class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = StatusUpdate
        fields = ["content"]
        labels = {"content": "Status Update"}

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "add a status update",
                }
            ),
        }
