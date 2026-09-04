from io import BytesIO

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import FormView
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import (
    RegistrationForm,
    UserProfileForm,
    BloodRequestForm,
    EmergencyRequestForm,
)
from .models import (
    UserProfile,
    BloodRequest,
    EmergencyRequest,
    DonationCertificate,
    Notification,
    EmergencyResponse,
)


# =========================================================
# HOME
# =========================================================

def home(request):
    return render(request, "accounts/home.html")

# =========================================================
# REGISTER
# =========================================================

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Create UserProfile if the form does not already create it
            profile, created = UserProfile.objects.get_or_create(
                user=user
            )

            # Copy registration information to profile
            profile.full_name = form.cleaned_data.get("full_name", "")
            profile.blood_group = form.cleaned_data.get("blood_group", "")
            profile.phone = form.cleaned_data.get("phone", "")
            profile.city = form.cleaned_data.get("city", "")
            profile.save()

            messages.success(
                request,
                "Registration successful! Please login."
            )
            return redirect("login")
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/registration.html",
        {"form": form}
    )


# =========================================================
# LOGIN
# =========================================================

class UserLoginView(FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(
            self.request,
            "Login successful!"
        )
        return redirect("dashboard")

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Invalid username or password."
        )
        return super().form_invalid(form)


# =========================================================
# LOGOUT
# =========================================================

def user_logout(request):
    logout(request)
    messages.success(
        request,
        "You have been logged out successfully."
    )
    return redirect("home")


# =========================================================
# DASHBOARD
# =========================================================

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    # Donors
    total_donors = UserProfile.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    recent_donors = (
        UserProfile.objects
        .select_related("user")
        .order_by("-id")[:5]
    )

    # Blood Requests
    total_requests = BloodRequest.objects.count()

    pending_requests = BloodRequest.objects.filter(
        status="Pending"
    ).count()

    fulfilled_requests = BloodRequest.objects.filter(
        status="Fulfilled"
    ).count()

    recent_requests = (
        BloodRequest.objects
        .order_by("-id")[:5]
    )

    # Blood group statistics
    blood_groups = [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    ]

    blood_group_stats = []

    for group in blood_groups:

        total = UserProfile.objects.filter(
            blood_group=group
        ).count()

        available = UserProfile.objects.filter(
            blood_group=group,
            is_available=True
        ).count()

        blood_group_stats.append({
            "group": group,
            "count": total,
            "available": available,
        })

    # Donations
    lives_saved = DonationCertificate.objects.count()

    # Emergency requests
    active_emergencies = EmergencyRequest.objects.filter(
        status="ACTIVE"
    ).count()

    context = {
        "profile": profile,

        "total_donors": total_donors,
        "available_donors": available_donors,

        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "fulfilled_requests": fulfilled_requests,

        "lives_saved": lives_saved,

        "blood_group_stats": blood_group_stats,

        "recent_requests": recent_requests,
        "recent_donors": recent_donors,

        "active_emergencies": active_emergencies,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context
    )

# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):
    profile_obj = request.user.userprofile

    if request.method == "POST":
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile_obj
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Profile updated successfully!"
            )
            return redirect("profile")

    else:
        form = UserProfileForm(instance=profile_obj)

    return render(
        request,
        "accounts/profile.html",
        {"form": form}
    )

# =========================================================
# DONOR DIRECTORY
# =========================================================

def donor_list(request):
    donors = UserProfile.objects.select_related(
        "user"
    ).filter(
        is_available=True
    )

    blood_group = request.GET.get("blood_group", "").strip()
    city = request.GET.get("city", "").strip()
    search = request.GET.get("search", "").strip()

    if blood_group:
        donors = donors.filter(
            blood_group__iexact=blood_group
        )

    if city:
        donors = donors.filter(
            city__icontains=city
        )

    if search:
        donors = donors.filter(
            Q(full_name__icontains=search)
            | Q(city__icontains=search)
            | Q(blood_group__icontains=search)
            | Q(user__username__icontains=search)
        )

    return render(
        request,
        "accounts/donor_list.html",
        {
            "donors": donors,
            "blood_group": blood_group,
            "city": city,
            "search": search,
        }
    )


# =========================================================
# DONOR DETAIL
# =========================================================

def donor_detail(request, id):
    donor = get_object_or_404(
        UserProfile.objects.select_related("user"),
        id=id
    )

    return render(
        request,
        "accounts/donor_detail.html",
        {
            "donor": donor,
        }
    )


# =========================================================
# REQUEST BLOOD
# =========================================================

def request_blood(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        form = BloodRequestForm(request.POST)

        if form.is_valid():
            blood_request = form.save()

            messages.success(
                request,
                "Blood request submitted successfully!"
            )

            return redirect("blood_requests")
    else:
        form = BloodRequestForm()

    return render(
        request,
        "accounts/request_blood.html",
        {
            "form": form,
        }
    )


# =========================================================
# BLOOD REQUEST LIST
# =========================================================

def blood_request_list(request):
    if not request.user.is_authenticated:
        return redirect("login")

    requests = BloodRequest.objects.all().order_by("-id")

    return render(
        request,
        "accounts/blood_request_list.html",
        {
            "requests": requests,
        }
    )


# =========================================================
# MATCHING DONORS
# =========================================================

def matching_donors(request, id):
    blood_request = get_object_or_404(
        BloodRequest,
        id=id
    )

    donors = UserProfile.objects.select_related(
        "user"
    ).filter(
        blood_group=blood_request.blood_group,
        is_available=True,
    )

    if blood_request.city:
        city_donors = donors.filter(
            city__icontains=blood_request.city
        )

        if city_donors.exists():
            donors = city_donors

    return render(
        request,
        "accounts/matching_donors.html",
        {
            "donors": donors,
            "blood_request": blood_request,
        }
    )


# =========================================================
# EMERGENCY REQUEST
# =========================================================

def emergency_request(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        form = EmergencyRequestForm(request.POST)

        if form.is_valid():
            emergency = form.save()

            messages.success(
                request,
                "Emergency blood request created successfully!"
            )

            # Create notifications for matching available donors
            matching_donors_qs = UserProfile.objects.filter(
                blood_group=emergency.blood_group,
                is_available=True,
            )

            for donor in matching_donors_qs:
                Notification.objects.create(
                    user=donor.user,
                    title="Emergency Blood Request",
                    message=(
                        f"Emergency blood required: "
                        f"{emergency.blood_group} - "
                        f"{emergency.units_required} unit(s). "
                        f"Hospital: {emergency.hospital_name}"
                    ),
                    emergency=emergency,
                )

            return redirect("dashboard")
    else:
        form = EmergencyRequestForm()

    return render(
        request,
        "accounts/emergency_request.html",
        {
            "form": form,
        }
    )


# =========================================================
# MARK DONATION
# =========================================================

def mark_donation(request, id):
    if not request.user.is_authenticated:
        return redirect("login")

    donor = get_object_or_404(
        UserProfile,
        id=id
    )

    donor.donation_count += 1
    donor.save()

    certificate = DonationCertificate.objects.create(
        donor=donor
    )

    messages.success(
        request,
        "Donation marked successfully!"
    )

    return redirect(
        "certificate",
        id=certificate.id
    )


# =========================================================
# DOWNLOAD DONATION CERTIFICATE
# =========================================================

def download_pdf(request, id):
    certificate = get_object_or_404(
        DonationCertificate.objects.select_related(
            "donor",
            "donor__user"
        ),
        id=id
    )

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # Border
    pdf.rect(
        35,
        35,
        width - 70,
        height - 70
    )

    # Title
    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawCentredString(
        width / 2,
        height - 100,
        "BLOODLINK"
    )

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawCentredString(
        width / 2,
        height - 140,
        "Blood Donation Certificate"
    )

    pdf.setFont(
        "Helvetica",
        12
    )

    donor_name = (
        certificate.donor.full_name
        or certificate.donor.user.username
    )

    pdf.drawCentredString(
        width / 2,
        height - 210,
        "This certificate is proudly presented to"
    )

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawCentredString(
        width / 2,
        height - 250,
        donor_name
    )

    pdf.setFont(
        "Helvetica",
        12
    )

    pdf.drawCentredString(
        width / 2,
        height - 300,
        "for making a valuable contribution through blood donation."
    )

    pdf.drawString(
        80,
        height - 370,
        f"Blood Group: {certificate.donor.blood_group}"
    )

    pdf.drawString(
        80,
        height - 400,
        f"Donation Date: {certificate.donation_date}"
    )

    pdf.drawString(
        80,
        height - 430,
        f"Certificate No: {certificate.certificate_number}"
    )

    pdf.setFont(
        "Helvetica-Oblique",
        11
    )

    pdf.drawCentredString(
        width / 2,
        90,
        "Thank you for helping save lives."
    )

    pdf.save()

    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="bloodlink_certificate_'
        f'{certificate.id}.pdf"'
    )

    return response


# =========================================================
# ABOUT
# =========================================================

def about(request):
    return render(
        request,
        "accounts/about.html"
    )


# =========================================================
# CONTACT
# =========================================================

def contact(request):
    if request.method == "POST":
        messages.success(
            request,
            "Thank you for contacting BloodLink!"
        )
        return redirect("contact")

    return render(
        request,
        "accounts/contact.html"
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

def notifications(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user_notifications = Notification.objects.filter(
        user=request.user
    ).select_related(
        "emergency"
    ).order_by("-created_at")

    if request.method == "POST":
        user_notifications.filter(
            is_read=False
        ).update(
            is_read=True
        )

        messages.success(
            request,
            "Notifications marked as read."
        )

        return redirect("notifications")

    return render(
        request,
        "accounts/notifications.html",
        {
            "notifications": user_notifications,
        }
    )


# =========================================================
# ACCEPT EMERGENCY
# =========================================================

def accept_emergency(request, emergency_id):
    if not request.user.is_authenticated:
        return redirect("login")

    emergency = get_object_or_404(
        EmergencyRequest,
        id=emergency_id
    )

    donor = get_object_or_404(
        UserProfile,
        user=request.user
    )

    response, created = EmergencyResponse.objects.get_or_create(
        emergency=emergency,
        donor=donor,
        defaults={
            "response": "ACCEPTED",
        }
    )

    if not created:
        response.response = "ACCEPTED"
        response.save()

    emergency.status = "MATCHED"
    emergency.save()

    

    messages.success(
        request,
        "You have accepted the emergency request."
    )

    return redirect("notifications")


# =========================================================
# REJECT EMERGENCY
# =========================================================

def reject_emergency(request, emergency_id):
    if not request.user.is_authenticated:
        return redirect("login")

    emergency = get_object_or_404(
        EmergencyRequest,
        id=emergency_id
    )

    donor = get_object_or_404(
        UserProfile,
        user=request.user
    )

    response, created = EmergencyResponse.objects.get_or_create(
        emergency=emergency,
        donor=donor,
        defaults={
            "response": "REJECTED",
        }
    )

    if not created:
        response.response = "REJECTED"
        response.save()

    messages.info(
        request,
        "You have rejected the emergency request."
    )

    return redirect("notifications")