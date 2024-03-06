from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from users.models import User
from django.forms.widgets import DateInput
from datetime import date


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
            self.fields[field_name].widget.attrs.update({"class": "form-control"})


class UserPasswordChangeForm(PasswordChangeForm):
    """
    Form for password change.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["old_password", "new_password1", "new_password2"]:
            self.fields[field_name].widget.attrs.update({"class": "form-control"})
