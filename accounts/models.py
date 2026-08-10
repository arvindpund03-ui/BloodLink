from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


# =========================================================
# USER PROFILE
# =========================================================

class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(
        max_length=100
    )

    blood_group = models.CharField(
        max_length=10
    )

    phone = models.CharField(
        max_length=15
    )

    city = models.CharField(
        max_length=100
    )

    photo = models.ImageField(
        upload_to="profile/",
        blank=True,
        null=True
    )

    emergency_contact = models.CharField(
        max_length=15,
        blank=True
    )

    is_available = models.BooleanField(
        default=True
    )

    location = models.CharField(
        max_length=255,
        blank=True
    )

    donation_count = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return self.full_name


# =========================================================
# DONATION CERTIFICATE
# =========================================================

class DonationCertificate(models.Model):

    donor = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE
    )

    donation_date = models.DateField(
        default=timezone.now
    )

    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        default=uuid.uuid4
    )

    def __str__(self):
        return self.certificate_number


# =========================================================
# NORMAL BLOOD REQUEST
# =========================================================

class BloodRequest(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Fulfilled", "Fulfilled"),
    ]

    patient_name = models.CharField(
        max_length=100
    )

    blood_group = models.CharField(
        max_length=10
    )

    city = models.CharField(
        max_length=100
    )

    hospital = models.CharField(
        max_length=100
    )

    contact_number = models.CharField(
        max_length=15
    )

    location = models.CharField(
        max_length=255,
        blank=True
    )

    emergency_contact = models.CharField(
        max_length=15,
        blank=True
    )

    units_required = models.PositiveIntegerField(
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return self.patient_name


# =========================================================
# 🚨 EMERGENCY BLOOD REQUEST
# =========================================================

class EmergencyRequest(models.Model):

    EMERGENCY_TYPE_CHOICES = [
        ("Accident", "Accident"),
        ("Surgery", "Surgery"),
        ("Emergency", "Emergency"),
        ("Other", "Other"),
    ]

    URGENCY_CHOICES = [
        ("CRITICAL", "CRITICAL"),
        ("HIGH", "HIGH"),
        ("NORMAL", "NORMAL"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "ACTIVE"),
        ("MATCHED", "MATCHED"),
        ("COMPLETED", "COMPLETED"),
        ("CANCELLED", "CANCELLED"),
    ]

    patient_name = models.CharField(
        max_length=100
    )

    blood_group = models.CharField(
        max_length=10
    )

    units_required = models.PositiveIntegerField(
        default=1
    )

    hospital_name = models.CharField(
        max_length=200
    )

    city = models.CharField(
        max_length=100
    )

    contact_number = models.CharField(
        max_length=15
    )

    emergency_type = models.CharField(
        max_length=50,
        choices=EMERGENCY_TYPE_CHOICES,
        default="Accident"
    )

    urgency = models.CharField(
        max_length=20,
        choices=URGENCY_CHOICES,
        default="HIGH"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.patient_name} - "
            f"{self.blood_group} - "
            f"{self.emergency_type}"
        )


# =========================================================
# OTP VERIFICATION
# =========================================================

class OTPVerification(models.Model):

    mobile = models.CharField(
        max_length=15
    )

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.mobile