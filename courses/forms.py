from django import forms

from courses.models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseMaterial,
    Feedback,
)


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
