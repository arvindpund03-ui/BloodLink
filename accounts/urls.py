from django.urls import path
from . import views

urlpatterns = [

# =========================
# HOME
# =========================

path(
    "",
    views.home,
    name="home"
),


# =========================
# AUTHENTICATION
# =========================

path(
    "register/",
    views.register,
    name="register"
),

path(
    "login/",
    views.UserLoginView.as_view(),
    name="login"
),

path(
    "logout/",
    views.user_logout,
    name="logout"
),


# =========================
# DASHBOARD
# =========================

path(
    "dashboard/",
    views.dashboard,
    name="dashboard"
),


# =========================
# PROFILE
# =========================

path(
    "profile/",
    views.profile,
    name="profile"
),


# =========================
# DONORS
# =========================

path(
    "donors/",
    views.donor_list,
    name="donors"
),

path(
    "donor/<int:id>/",
    views.donor_detail,
    name="donor_detail"
),


# =========================
# BLOOD REQUEST
# =========================

path(
    "request-blood/",
    views.request_blood,
    name="request_blood"
),

path(
    "blood-requests/",
    views.blood_request_list,
    name="blood_requests"
),

path(
    "matching-donors/<int:id>/",
    views.matching_donors,
    name="matching_donors"
),


# =========================
# EMERGENCY REQUEST
# =========================

path(
    "emergency-request/",
    views.emergency_request,
    name="emergency_request"
),


# =========================
# DONATION
# =========================

path(
    "mark-donation/<int:id>/",
    views.mark_donation,
    name="mark_donation"
),


# =========================
# CERTIFICATE PDF
# =========================

path(
    "certificate/<int:id>/",
    views.download_pdf,
    name="certificate"
),


# =========================
# STATIC PAGES
# =========================

path(
    "about/",
    views.about,
    name="about"
),

path(
    "contact/",
    views.contact,
    name="contact"
),

]