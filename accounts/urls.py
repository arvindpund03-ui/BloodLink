from django.urls import path
from . import views
from .api_views import (
    api_home,
    api_login,
    api_donors,
)
urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.user_logout, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("profile/", views.profile, name="profile"),

    path("donors/", views.donor_list, name="donor_list"),
    
    path("donor/<int:id>/", views.donor_detail, name="donor_detail"),

    path("request-blood/", views.request_blood, name="request_blood"),

    path("blood-requests/", views.blood_request_list, name="blood_request_list"),

    path("matching-donors/<int:id>/", views.matching_donors, name="matching_donors"),

    path("emergency-request/", views.emergency_request, name="emergency_request"),

    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("notifications/", views.notifications, name="notifications"),
    
]