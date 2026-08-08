from django.contrib import admin
from .models import UserProfile, BloodRequest


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = [
        "full_name",
        "blood_group",
        "phone",
        "city",
        "donation_count",
        "is_available",
    ]

    search_fields = [
        "full_name",
        "blood_group",
        "city",
    ]

    list_filter = [
        "blood_group",
        "city",
        "is_available",
    ]

    fields = [
        "user",
        "full_name",
        "blood_group",
        "phone",
        "city",
        "photo",
        "emergency_contact",
        "location",
        "is_available",
        "donation_count",
    ]


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):

    list_display = [
        "patient_name",
        "blood_group",
        "city",
        "hospital",
        "units_required",
    ]

    search_fields = [
        "patient_name",
        "blood_group",
        "city",
    ]

    list_filter = [
        "blood_group",
        "city",
    ]
print("UserProfile admin loaded")