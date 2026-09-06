from django.urls import path

from . import views
from . import api_views


urlpatterns = [

    # =========================
    # MAIN PAGES
    # =========================

    path("", views.home, name="home"),

    path("register/", views.register, name="register"),

    path("login/", views.UserLoginView.as_view(), name="login"),

    path("logout/", views.user_logout, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("profile/", views.profile, name="profile"),

   


    # =========================
    # DONORS
    # =========================

    path("donors/", views.donor_list, name="donor_list"),

    path(
        "donor/<int:id>/",
        views.donor_detail,
        name="donor_detail"
    ),

    path(
        "matching-donors/<int:id>/",
        views.matching_donors,
        name="matching_donors"
    ),


    # =========================
    # BLOOD REQUESTS
    # =========================

    path(
        "request-blood/",
        views.request_blood,
        name="request_blood"
    ),

    path(
        "blood-requests/",
        views.blood_request_list,
        name="blood_request_list"
    ),


    # =========================
    # EMERGENCY
    # =========================

    path(
        "emergency-request/",
        views.emergency_request,
        name="emergency_request"
    ),

    path(
        "emergency/<int:emergency_id>/accept/",
        views.accept_emergency,
        name="accept_emergency"
    ),

    path(
        "emergency/<int:emergency_id>/reject/",
        views.reject_emergency,
        name="reject_emergency"
    ),


    # =========================
    # DONATION
    # =========================

    path(
        "mark-donation/<int:id>/",
        views.mark_donation,
        name="mark_donation"
    ),

    path(
        "certificate/<int:id>/",
        views.download_pdf,
        name="certificate"
    ),


    # =========================
    # OTHER PAGES
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

    path(
        "notifications/",
        views.notifications,
        name="notifications"
    ),


    # =========================
    # API
    # =========================

    path(
        "api/",
        api_views.api_home,
        name="api_home"
    ),

    path(
    "verify-certificate/<str:certificate_number>/",
    views.verify_certificate,
    name="verify_certificate"
    ),

    path("dashboard/", views.dashboard, name="dashboard"),


path(
    "api/admin-active-emergencies/",
    views.admin_active_emergency_api,
    name="admin_active_emergencies"
),



]