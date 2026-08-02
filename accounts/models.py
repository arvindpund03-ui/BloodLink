from django.db import models
from django.contrib.auth.models import User


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


    def __str__(self):
        return self.full_name



class BloodRequest(models.Model):

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

    units_required = models.IntegerField()


    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Fulfilled", "Fulfilled"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )


    def __str__(self):
        return self.patient_name