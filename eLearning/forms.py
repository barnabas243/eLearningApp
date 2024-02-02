from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from .models import User,Course  # Import your User model
from django.forms.widgets import DateInput
from datetime import date

class UserLoginForm(AuthenticationForm):
    """
    Form for user authentication.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'password']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

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
    dob = forms.DateField(
        label="Date of Birth",
        widget=DateInput(attrs={'type': 'date', 'min': '1900-01-01', 'max': today}),
    )


    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'user_type', 'dob')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_order = ['username', 'email', 'first_name', 'last_name', 'user_type', 'dob', 'password1', 'password2']
        for field_name in field_order:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        """
        Save the user instance.
        """
        
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        user.dob = self.cleaned_data['dob']
        if commit:
            user.save()
        return user
            
class UserPasswordChangeForm(PasswordChangeForm):
    """
    Form for password change.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['old_password', 'new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

class ProfilePictureForm(forms.Form):
    profile_picture = forms.ImageField()

    def save(self, user):
        # Get the uploaded file
        profile_picture = self.cleaned_data['profile_picture']
        # Save the file to the user's profile_picture field or any other desired location
        user.profile_picture = profile_picture
        user.save()
        
class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description','duration_weeks']  # Add other fields as needed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form fields if needed
        self.fields['name'].label = 'Course Name'
        self.fields['description'].label = 'Description'
        
class MaterialUploadForm(forms.Form):
    file = forms.FileField()
    week_number = forms.IntegerField(widget=forms.HiddenInput)
    course = forms.CharField(widget=forms.HiddenInput)
