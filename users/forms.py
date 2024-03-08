from django import forms
from users.models import StatusUpdate, User

from users.tasks import process_image


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["photo"]

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Call Celery task to process the image
        # if instance.photo:
        #     process_image.delay(instance.photo.path)

        if commit:
            instance.save()

        return instance


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
