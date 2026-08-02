from django.contrib import admin

from .models import UserProfile, BloodRequest


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = [
        "full_name",
        "blood_group",
        "phone",
        "city"
    ]

    search_fields = [
        "full_name",
        "blood_group",
        "city"
    ]

    list_filter = [
        "blood_group",
        "city"
    ]


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):

    list_display = [
        "patient_name",
        "blood_group",
        "city",
        "hospital",
        "units_required"
    ]

    search_fields = [
        "patient_name",
        "blood_group",
        "city"
    ]

    list_filter = [
        "blood_group",
        "city"
    ]