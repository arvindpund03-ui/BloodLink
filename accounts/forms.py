from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile, BloodRequest, EmergencyRequest


class RegistrationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove username help text
        self.fields["username"].help_text = ""

        # Remove password help text
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile

        fields = [
            "full_name",
            "blood_group",
            "phone",
            "city",
            "is_available",
            "photo",
        ]


class BloodRequestForm(forms.ModelForm):

    class Meta:
        model = BloodRequest

        fields = [
            "patient_name",
            "blood_group",
            "city",
            "hospital",
            "units_required",
            "status",
        ]


class EmergencyRequestForm(forms.ModelForm):

    class Meta:
        model = EmergencyRequest

        fields = [
            "patient_name",
            "blood_group",
            "units_required",
            "hospital_name",
            "city",
            "contact_number",
            "emergency_type",
            "urgency",
        ]

        widgets = {
            "patient_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Patient Name",
            }),

            "blood_group": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Blood Group e.g. O+",
            }),

            "units_required": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
            }),

            "hospital_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Hospital Name",
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "City",
            }),

            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Emergency Contact Number",
            }),

            "emergency_type": forms.Select(attrs={
                "class": "form-select",
            }),

            "urgency": forms.Select(attrs={
                "class": "form-select",
            }),
        }