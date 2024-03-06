from django import forms
from users.models import StatusUpdate


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
