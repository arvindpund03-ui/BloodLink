from django.urls import path
from . import views
from django.urls import path
from . import views
from .views import (
    home,
    register,
    UserLoginView,
    dashboard,
    user_logout,
    profile,
    donor_list,
    donor_detail,
    request_blood,
    blood_request_list,
    matching_donors,
    about,
    contact,
)


urlpatterns = [
    path('send-otp/',views.send_otp,name='send_otp'),

    path('verify-otp/',views.verify_otp,name='verify_otp'),

    path("home", home, name="home"),

    path("register/", register, name="register"),

    path("login/", UserLoginView.as_view(), name="login"),

    path("dashboard/", dashboard, name="dashboard"),

    path("logout/", user_logout, name="logout"),

    path("profile/", profile, name="profile"),

    path("donors/", donor_list, name="donor_list"),

    path("donor/<int:id>/", donor_detail, name="donor_detail"),

    path("request-blood/", request_blood, name="request_blood"),

    path("blood-requests/", blood_request_list, name="blood_request_list"),

    path("matching-donors/<int:id>/", matching_donors, name="matching_donors"),

    path("about/", about, name="about"),

    path("contact/", contact, name="contact"),
    
    path("download-pdf/", views.download_pdf, name="download_pdf"),
]




