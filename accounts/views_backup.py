from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from .models import UserProfile, BloodRequest, EmergencyRequest, DonationCertificate

from .models import (
    UserProfile,
    BloodRequest,
    EmergencyRequest,
    DonationCertificate,
)


@login_required
def dashboard(request):
    total_donors = UserProfile.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    total_requests = BloodRequest.objects.count()

    pending_requests = BloodRequest.objects.filter(
        status="Pending"
    ).count()

    fulfilled_requests = BloodRequest.objects.filter(
        status="Fulfilled"
    ).count()

    active_emergencies = EmergencyRequest.objects.filter(
        status="ACTIVE"
    ).count()

    lives_saved = DonationCertificate.objects.count()

    blood_groups = [
        "A+", "A-", "B+", "B-",
        "O+", "O-", "AB+", "AB-"
    ]

    blood_group_stats = []

    for group in blood_groups:
        count = UserProfile.objects.filter(
            blood_group__iexact=group
        ).count()

        available = UserProfile.objects.filter(
            blood_group__iexact=group,
            is_available=True
        ).count()

        blood_group_stats.append({
            "group": group,
            "count": count,
            "available": available,
        })

    recent_requests = BloodRequest.objects.order_by("-id")[:6]
    recent_donors = UserProfile.objects.order_by("-id")[:6]

    context = {
        "total_donors": total_donors,
        "available_donors": available_donors,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "fulfilled_requests": fulfilled_requests,
        "active_emergencies": active_emergencies,
        "lives_saved": lives_saved,
        "blood_group_stats": blood_group_stats,
        "recent_requests": recent_requests,
        "recent_donors": recent_donors,
    }

    return render(request, "dashboard.html", context)


def donor_list(request):
    donors = UserProfile.objects.all()

    blood_group = request.GET.get(
        "blood_group", ""
    ).strip()

    city = request.GET.get(
        "city", ""
    ).strip()

    available = request.GET.get(
        "available", ""
    ).strip()

    if blood_group:
        donors = donors.filter(
            blood_group__iexact=blood_group
        )

    if city:
        donors = donors.filter(
            city__icontains=city
        )

    if available == "1":
        donors = donors.filter(
            is_available=True
        )

    donors = donors.order_by("-id")

    return render(
        request,
        "donor_list.html",
        {
            "donors": donors,
            "selected_blood_group": blood_group,
            "selected_city": city,
            "available_only": available == "1",
        },
    )