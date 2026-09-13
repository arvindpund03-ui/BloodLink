from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import (
    UserProfile,
    BloodRequest,
    EmergencyRequest,
)


# =========================================================
# BLOOD GROUP CONSTANTS
# =========================================================

BLOOD_GROUP_CHOICES = [
    ("A+", "A+"),
    ("A-", "A-"),
    ("B+", "B+"),
    ("B-", "B-"),
    ("AB+", "AB+"),
    ("AB-", "AB-"),
    ("O+", "O+"),
    ("O-", "O-"),
]

VALID_BLOOD_GROUPS = {
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
}


# =========================================================
# REGISTRATION FORM
# =========================================================

class RegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter email address"
            }
        )
    )

    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter full name"
            }
        )
    )

    blood_group = forms.ChoiceField(
        choices=[
            ("", "Select Blood Group")
        ] + BLOOD_GROUP_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter phone number"
            }
        )
    )

    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter city"
            }
        )
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

    # -----------------------------------------------------
    # INITIALIZE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # EMAIL VALIDATION
    # -----------------------------------------------------

    def clean_email(self):

        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(email__iexact=email).exists():

            raise forms.ValidationError(
                "This email address is already registered."
            )

        return email

    # -----------------------------------------------------
    # PHONE VALIDATION
    # -----------------------------------------------------

    def clean_phone(self):

        phone = self.cleaned_data["phone"].strip()

        cleaned_phone = phone.replace(
            " ",
            ""
        ).replace(
            "-",
            ""
        )

        if not cleaned_phone.isdigit():

            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        if len(cleaned_phone) < 10:

            raise forms.ValidationError(
                "Phone number must contain at least 10 digits."
            )

        return phone

    # -----------------------------------------------------
    # SAVE USER + PROFILE
    # -----------------------------------------------------

    def save(self, commit=True):

        user = super().save(commit=False)

        user.email = self.cleaned_data[
            "email"
        ].lower().strip()

        if commit:

            user.save()

            UserProfile.objects.update_or_create(

                user=user,

                defaults={

                    "full_name":
                        self.cleaned_data[
                            "full_name"
                        ].strip(),

                    "blood_group":
                        self.cleaned_data[
                            "blood_group"
                        ],

                    "phone":
                        self.cleaned_data[
                            "phone"
                        ].strip(),

                    "city":
                        self.cleaned_data[
                            "city"
                        ].strip(),

                    "is_available": True,
                }
            )

        return user


# =========================================================
# USER PROFILE FORM
# =========================================================

class UserProfileForm(forms.ModelForm):

    blood_group = forms.ChoiceField(
        choices=[
            ("", "Select Blood Group")
        ] + BLOOD_GROUP_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )

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

            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter full name"
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter phone number"
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city"
                }
            ),

            "photo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "emergency_contact": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter emergency contact"
                }
            ),

            "is_available": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),

            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter location"
                }
            ),
        }

    # -----------------------------------------------------
    # CLEAN PHONE
    # -----------------------------------------------------

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone",
            ""
        ).strip()

        if phone:

            cleaned_phone = phone.replace(
                " ",
                ""
            ).replace(
                "-",
                ""
            )

            if not cleaned_phone.isdigit():

                raise forms.ValidationError(
                    "Enter a valid phone number."
                )

        return phone


# =========================================================
# NORMAL BLOOD REQUEST FORM
# =========================================================

class BloodRequestForm(forms.ModelForm):

    blood_group = forms.ChoiceField(
        choices=[
            ("", "Select Required Blood Group")
        ] + BLOOD_GROUP_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )

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

            "patient_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter patient name"
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city"
                }
            ),

            "hospital": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter hospital name"
                }
            ),

            "contact_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter contact number"
                }
            ),

            "units_required": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Number of blood units"
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),
        }

    # -----------------------------------------------------
    # VALIDATE PHONE
    # -----------------------------------------------------

    def clean_contact_number(self):

        contact_number = self.cleaned_data[
            "contact_number"
        ].strip()

        cleaned_number = contact_number.replace(
            " ",
            ""
        ).replace(
            "-",
            ""
        )

        if not cleaned_number.isdigit():

            raise forms.ValidationError(
                "Enter a valid contact number."
            )

        if len(cleaned_number) < 10:

            raise forms.ValidationError(
                "Contact number must contain at least 10 digits."
            )

        return contact_number

    # -----------------------------------------------------
    # VALIDATE UNITS
    # -----------------------------------------------------

    def clean_units_required(self):

        units = self.cleaned_data[
            "units_required"
        ]

        if units < 1:

            raise forms.ValidationError(
                "At least 1 blood unit is required."
            )

        return units


# =========================================================
# EMERGENCY BLOOD REQUEST FORM
# =========================================================

class EmergencyRequestForm(forms.ModelForm):

    blood_group = forms.ChoiceField(
        choices=[
            ("", "Select Required Blood Group")
        ] + BLOOD_GROUP_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )

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

            "patient_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter patient name"
                }
            ),

            "units_required": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Number of units required"
                }
            ),

            "hospital_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter hospital name"
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city"
                }
            ),

            "contact_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter emergency contact number"
                }
            ),

            "emergency_type": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "urgency": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),
        }

    # -----------------------------------------------------
    # CLEAN PATIENT NAME
    # -----------------------------------------------------

    def clean_patient_name(self):

        patient_name = self.cleaned_data[
            "patient_name"
        ].strip()

        if len(patient_name) < 2:

            raise forms.ValidationError(
                "Please enter a valid patient name."
            )

        return patient_name

    # -----------------------------------------------------
    # CLEAN HOSPITAL
    # -----------------------------------------------------

    def clean_hospital_name(self):

        hospital_name = self.cleaned_data[
            "hospital_name"
        ].strip()

        if len(hospital_name) < 2:

            raise forms.ValidationError(
                "Please enter a valid hospital name."
            )

        return hospital_name

    # -----------------------------------------------------
    # CLEAN CITY
    # -----------------------------------------------------

    def clean_city(self):

        city = self.cleaned_data[
            "city"
        ].strip()

        if len(city) < 2:

            raise forms.ValidationError(
                "Please enter a valid city."
            )

        return city

    # -----------------------------------------------------
    # CLEAN CONTACT NUMBER
    # -----------------------------------------------------

    def clean_contact_number(self):

        contact_number = self.cleaned_data[
            "contact_number"
        ].strip()

        cleaned_number = contact_number.replace(
            " ",
            ""
        ).replace(
            "-",
            ""
        )

        if not cleaned_number.isdigit():

            raise forms.ValidationError(
                "Enter a valid contact number."
            )

        if len(cleaned_number) < 10:

            raise forms.ValidationError(
                "Contact number must contain at least 10 digits."
            )

        return contact_number

    # -----------------------------------------------------
    # CLEAN UNITS
    # -----------------------------------------------------

    def clean_units_required(self):

        units = self.cleaned_data[
            "units_required"
        ]

        if units < 1:

            raise forms.ValidationError(
                "At least 1 blood unit is required."
            )

        if units > 50:

            raise forms.ValidationError(
                "Please enter a realistic number of blood units."
            )

        return units