from django import forms
from .models import UserProfile, BloodRequest
from django.contrib.auth.models import User


class RegistrationForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password"
        ]


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