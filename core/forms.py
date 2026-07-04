from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Ambulance,
    Appointment,
    BloodRequest,
    BloodUnit,
    Dispatch,
    Donor,
    Hospital,
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
        fields = ["blood_type", "date_of_birth", "county", "weight_kg", "last_donation_date"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "last_donation_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {"weight_kg": "Weight (kg)"}


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


# ---------------------------------------------------------------------------
# Admin control-panel forms (full CRUD, used by the system administrator)
# ---------------------------------------------------------------------------

class AdminUserForm(forms.ModelForm):
    """Create/edit any user. Password optional on edit, required on create."""

    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Leave blank to keep the current password (required for new users).",
    )

    class Meta:
        model = User
        fields = ["username", "email", "role", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields["password"].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class AdminDonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ["user", "blood_type", "date_of_birth", "county", "weight_kg", "last_donation_date"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "last_donation_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {"weight_kg": "Weight (kg)"}


class AdminHospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ["name", "county", "manager"]


class AdminBloodUnitForm(forms.ModelForm):
    class Meta:
        model = BloodUnit
        fields = ["hospital", "blood_type", "collection_date", "is_used"]
        widgets = {"collection_date": forms.DateInput(attrs={"type": "date"})}


class AdminBloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ["hospital", "blood_type", "units_needed", "priority", "status"]


class AdminAmbulanceForm(forms.ModelForm):
    class Meta:
        model = Ambulance
        fields = ["operator", "plate_number", "county", "is_available"]


class AdminAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["donor", "hospital", "date", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class AdminDispatchForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = ["request", "ambulance", "status"]
