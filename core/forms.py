from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Appointment,
    BloodRequest,
    BloodUnit,
    Donor,
    User,
    BLOOD_TYPES,
)


class UserRegistrationForm(UserCreationForm):
    blood_type = forms.ChoiceField(
        choices=BLOOD_TYPES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "blood_type", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.DONOR and not cleaned.get("blood_type"):
            self.add_error("blood_type", "Blood group is required for donors.")
        return cleaned

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


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ["blood_type", "date_of_birth", "county", "last_donation_date"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "last_donation_date": forms.DateInput(attrs={"type": "date"}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["hospital", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class BloodUnitForm(forms.ModelForm):
    class Meta:
        model = BloodUnit
        fields = ["blood_type", "collection_date"]
        widgets = {"collection_date": forms.DateInput(attrs={"type": "date"})}


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ["blood_type", "units_needed", "priority"]
