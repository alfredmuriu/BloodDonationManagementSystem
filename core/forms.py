from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Donor, User


class UserRegistrationForm(UserCreationForm):
    blood_type = forms.ChoiceField(
        choices=Donor.BLOOD_TYPES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ("username", "role", "blood_type", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if user.role == User.Role.DONOR:
                Donor.objects.create(
                    user=user,
                    blood_type=self.cleaned_data.get("blood_type") or "O+",
                )
        return user
