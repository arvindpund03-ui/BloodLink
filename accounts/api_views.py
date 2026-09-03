from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import UserProfile


# =========================================================
# API HOME
# GET /api/
# =========================================================

@api_view(["GET"])
def api_home(request):
    return Response({
        "success": True,
        "message": "Welcome to BloodLink API",
        "version": "1.0"
    })


# =========================================================
# API LOGIN
# POST /api/login/
# =========================================================

@api_view(["POST"])
def api_login(request):

    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {
                "success": False,
                "message": "Username and password are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(
        username=username,
        password=password
    )

    if user is None:
        return Response(
            {
                "success": False,
                "message": "Invalid username or password"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response({
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    })


# =========================================================
# API DONORS
# GET /api/donors/
# Example:
# /api/donors/?city=Pune
# /api/donors/?blood_group=A+
# =========================================================

@api_view(["GET"])
def api_donors(request):

    city = request.GET.get("city")
    blood_group = request.GET.get("blood_group")

    donors = UserProfile.objects.filter(
        is_available=True
    )

    if city:
        donors = donors.filter(
            city__iexact=city
        )

    if blood_group:
        donors = donors.filter(
            blood_group=blood_group
        )

    donor_list = []

    for profile in donors:

        donor_list.append({
            "id": profile.user.id,
            "name": profile.user.get_full_name()
                    or profile.user.username,
            "blood_group": profile.blood_group,
            "city": profile.city,
        })

    return Response({
        "success": True,
        "count": len(donor_list),
        "donors": donor_list
    })