from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import (
    UserProfile,
    BloodRequest,
    EmergencyRequest,
)


# =========================================================
# REGISTRATION FORM
# =========================================================

class RegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email"
        })
    )

    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter full name"
        })
    )

    blood_group = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Example: A+"
        })
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter phone number"
        })
    )

    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter city"
        })
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "full_name",
            "blood_group",
            "phone",
            "city",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter username"
        })

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm password"
        })

    def save(self, commit=True):

        # Save Django User
        user = super().save(commit=commit)

        # Create UserProfile automatically
        if commit:

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": self.cleaned_data["full_name"],
                    "blood_group": self.cleaned_data["blood_group"].upper().strip(),
                    "phone": self.cleaned_data["phone"],
                    "city": self.cleaned_data["city"],
                    "is_available": True,
                }
            )

        return user


# =========================================================
# USER PROFILE FORM
# =========================================================

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile

        fields = [
            "full_name",
            "blood_group",
            "phone",
            "city",
            "photo",
            "emergency_contact",
            "is_available",
            "location",
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter full name"
            }),

            "blood_group": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: A+"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number"
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city"
            }),

            "photo": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),

            "emergency_contact": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter emergency contact"
            }),

            "is_available": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter location"
            }),
        }


# =========================================================
# NORMAL BLOOD REQUEST FORM
# =========================================================

class BloodRequestForm(forms.ModelForm):

    class Meta:
        model = BloodRequest

        fields = [
            "patient_name",
            "blood_group",
            "city",
            "hospital",
            "contact_number",
            "units_required",
            "status",
        ]

        widgets = {
            "patient_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter patient name"
            }),

            "blood_group": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: A+"
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city"
            }),

            "hospital": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter hospital name"
            }),

            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter contact number"
            }),

            "units_required": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),
        }


# =========================================================
# EMERGENCY BLOOD REQUEST FORM
# =========================================================

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
            "status",
        ]

        widgets = {
            "patient_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter patient name"
            }),

            "blood_group": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: A+"
            }),

            "units_required": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),

            "hospital_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter hospital name"
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city"
            }),

            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter contact number"
            }),

            "emergency_type": forms.Select(attrs={
                "class": "form-select"
            }),

            "urgency": forms.Select(attrs={
                "class": "form-select"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),
        }