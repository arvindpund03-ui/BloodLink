from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
from .models import (
    UserProfile,
    BloodRequest,
    OTPVerification,
    DonationCertificate,
)

from .forms import (
    RegistrationForm,
    UserProfileForm,
    BloodRequestForm,
)

from django.core.mail import send_mail
from django.conf import settings

from datetime import datetime

import os
import requests

from .utils import generate_otp

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Image,
)
from reportlab.lib.enums import TA_CENTER


#Home View

def home(request):

    total_donors = UserProfile.objects.count()

    total_requests = BloodRequest.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    recent_requests = BloodRequest.objects.order_by("-id")[:5]

    return render(
        request,
        "home.html",
        {
            "total_donors": total_donors,
            "total_requests": total_requests,
            "available_donors": available_donors,
            "recent_requests": recent_requests,
        },
    )


#Register View

def register(request):

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(form.cleaned_data["password"])

            user.save()

            messages.success(
                request,
                "Registration Successful"
            )

            return redirect("/login/")

    else:

        form = RegistrationForm()

    return render(
        request,
        "accounts/registration.html",
        {
            "form": form
        }
    )


#Login View

class UserLoginView(LoginView):

    template_name = "accounts/login.html"

#Dashboard

@login_required
def dashboard(request):

    total_donors = UserProfile.objects.count()

    total_requests = BloodRequest.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    blood_stats = UserProfile.objects.values(
        "blood_group"
    ).annotate(
        total=Count("id")
    )

    latest_donors = UserProfile.objects.order_by("-id")[:5]

    recent_requests = BloodRequest.objects.order_by("-id")[:5]

    return render(
        request,
        "accounts/dashboard.html",
        {
            "total_donors": total_donors,
            "total_requests": total_requests,
            "available_donors": available_donors,
            "blood_stats": blood_stats,
            "latest_donors": latest_donors,
            "recent_requests": recent_requests,
        },
    )

#Logout

def user_logout(request):

    logout(request)

    return redirect("/login/")

#Profile

@login_required
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():

            profile = form.save(commit=False)

            profile.user = request.user

            profile.save()

            messages.success(
                request,
                "Profile Updated Successfully."
            )

            return redirect("/profile/")

    else:

        form = UserProfileForm(
            instance=profile
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form
        },
    )

@login_required
def donor_list(request):
    donors = UserProfile.objects.all()

    blood_group = request.GET.get("blood_group")
    city = request.GET.get("city")

    if blood_group:
        donors = donors.filter(
            blood_group=blood_group
        )

    if city:
        donors = donors.filter(
            city__icontains=city
        )

    return render(
        request,
        "accounts/donor_list.html",
        {
            "donors": donors
        }
    )


@login_required
def donor_detail(request, id):
    donor = UserProfile.objects.get(id=id)

    return render(
        request,
        "accounts/donor_detail.html",
        {
            "donor": donor
        }
    )


@login_required
def request_blood(request):

    if request.method == "POST":

        form = BloodRequestForm(request.POST)

        if form.is_valid():

            blood_request = form.save()

            emails = UserProfile.objects.filter(
                blood_group=blood_request.blood_group,
                city=blood_request.city,
                is_available=True
            ).exclude(
                user__email=""
            ).values_list(
                "user__email",
                flat=True
            )

            if emails:
                send_mail(
                    subject="🩸 Urgent Blood Request - BloodLink",
                    message=f"""
New Blood Request

Patient: {blood_request.patient_name}
Blood Group: {blood_request.blood_group}
City: {blood_request.city}

If you are available, please contact the patient.

BloodLink Team
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=list(emails),
                    fail_silently=False,
                )

            messages.success(
                request,
                "Blood request submitted successfully!"
            )

            return redirect("/dashboard/")

    else:
        form = BloodRequestForm()

    return render(
        request,
        "accounts/request_blood.html",
        {
            "form": form
        }
    )

@login_required
def blood_request_list(request):

    requests = BloodRequest.objects.all().order_by("-id")

    return render(
        request,
        "accounts/blood_request_list.html",
        {
            "requests": requests
        }
    )


@login_required
def matching_donors(request, id):

    blood_request = BloodRequest.objects.get(id=id)

    donors = UserProfile.objects.filter(
        blood_group=blood_request.blood_group,
        city=blood_request.city,
        is_available=True
    )

    return render(
        request,
        "accounts/matching_donors.html",
        {
            "blood_request": blood_request,
            "donors": donors
        }
    )


def about(request):
    return render(
        request,
        "accounts/about.html"
    )


def contact(request):
    return render(
        request,
        "accounts/contact.html"
    )

@staff_member_required
def mark_donation(request, id):

    donor = UserProfile.objects.filter(
        id=id
    ).first()

    if not donor:
        messages.error(
            request,
            "Donor not found."
        )
        return redirect("/dashboard/")

    donor.donation_count += 1
    donor.is_available = False
    donor.save()

    messages.success(
        request,
        f"Donation recorded for {donor.full_name}."
    )

    return redirect("/dashboard/")

@login_required
def donation_certificate(request, id):

    donor = UserProfile.objects.filter(
        id=id,
        user=request.user
    ).first()

    # दुसऱ्या user चा certificate access करण्याचा प्रयत्न
    if not donor:
        messages.error(
            request,
            "You are not authorized to access this certificate."
        )
        return redirect("/dashboard/")

    # Donation केलेली नसेल
    if donor.donation_count <= 0:
        messages.error(
            request,
            "Certificate is available only after completing a blood donation."
        )
        return redirect("/dashboard/")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Donation_Certificate.pdf"'
    )

    p = canvas.Canvas(
        response,
        pagesize=A4
    )

    p.setFont(
        "Helvetica-Bold",
        24
    )

    p.drawCentredString(
        300,
        780,
        "Blood Donation Certificate"
    )

    p.setFont(
        "Helvetica",
        16
    )

    p.drawCentredString(
        300,
        720,
        f"This certificate is awarded to {donor.full_name}"
    )

    p.drawCentredString(
        300,
        690,
        "For Voluntarily Donating Blood"
    )

    p.drawCentredString(
        300,
        660,
        f"Blood Group: {donor.blood_group}"
    )

    p.drawCentredString(
        300,
        630,
        f"City: {donor.city}"
    )

    p.drawCentredString(
        300,
        600,
        f"Donation Count: {donor.donation_count}"
    )

    p.drawCentredString(
        300,
        570,
        f"Date: {datetime.now().strftime('%d-%m-%Y')}"
    )

    p.setFont(
        "Helvetica-Bold",
        14
    )

    p.drawCentredString(
        300,
        520,
        "Thank You For Saving A Life!"
    )

    p.showPage()
    p.save()

    return response

@login_required
def download_pdf(request):

    # Get logged-in user's donor profile
    donor = UserProfile.objects.filter(
        user=request.user
    ).first()

    # Profile not found
    if not donor:
        messages.error(
            request,
            "Please complete your donor profile first."
        )
        return redirect("/profile/")

    # Certificate only after donation
    if donor.donation_count <= 0:
        messages.error(
            request,
            "Certificate is available only after completing a blood donation."
        )
        return redirect("/dashboard/")

    # Create PDF response
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="BloodLink_Donation_Certificate.pdf"'
    )

    # Create PDF
    p = canvas.Canvas(
        response,
        pagesize=A4
    )

    width, height = A4

    # =====================================
    # BACKGROUND
    # =====================================

    p.setFillColor(colors.white)

    p.rect(
        0,
        0,
        width,
        height,
        fill=1,
        stroke=0
    )

    # =====================================
    # OUTER RED BORDER
    # =====================================

    p.setStrokeColor(
        colors.HexColor("#b71c1c")
    )

    p.setLineWidth(8)

    p.rect(
        20,
        20,
        width - 40,
        height - 40,
        fill=0,
        stroke=1
    )

    # =====================================
    # INNER RED BORDER
    # =====================================

    p.setStrokeColor(
        colors.HexColor("#d32f2f")
    )

    p.setLineWidth(2)

    p.rect(
        35,
        35,
        width - 70,
        height - 70,
        fill=0,
        stroke=1
    )

    # =====================================
    # LOGO
    # =====================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "bloodlink",
        "static",
        "image",
        "logo.png"
    )

    if os.path.exists(logo_path):

        p.drawImage(
            logo_path,
            235,
            720,
            width=125,
            height=65,
            preserveAspectRatio=True,
            mask="auto"
        )

    else:

        # Fallback if logo is missing
        p.setFillColor(
            colors.HexColor("#d71920")
        )

        p.setFont(
            "Helvetica-Bold",
            30
        )

        p.drawCentredString(
            width / 2,
            745,
            "BloodLink"
        )

    # =====================================
    # TAGLINE
    # =====================================

    p.setFillColor(
        colors.HexColor("#263238")
    )

    p.setFont(
        "Helvetica",
        9
    )

    p.drawCentredString(
        width / 2,
        710,
        "SAVE BLOOD, SAVE LIFE"
    )

    # =====================================
    # CERTIFICATE TITLE
    # =====================================

    p.setFillColor(
        colors.HexColor("#9e0000")
    )

    p.setFont(
        "Helvetica-Bold",
        30
    )

    p.drawCentredString(
        width / 2,
        655,
        "CERTIFICATE"
    )

    p.setFillColor(
        colors.HexColor("#263238")
    )

    p.setFont(
        "Helvetica-Bold",
        17
    )

    p.drawCentredString(
        width / 2,
        625,
        "OF APPRECIATION"
    )

    # Decorative line
    p.setStrokeColor(
        colors.HexColor("#b71c1c")
    )

    p.setLineWidth(1)

    p.line(
        155,
        608,
        width - 155,
        608
    )

    # =====================================
    # PRESENTED TO
    # =====================================

    p.setFillColor(
        colors.HexColor("#263238")
    )

    p.setFont(
        "Helvetica",
        13
    )

    p.drawCentredString(
        width / 2,
        565,
        "This certificate is proudly presented to"
    )

    # =====================================
    # DONOR NAME
    # =====================================

    p.setFillColor(
        colors.HexColor("#9e0000")
    )

    p.setFont(
        "Helvetica-Bold",
        25
    )

    p.drawCentredString(
        width / 2,
        525,
        donor.full_name
    )

    p.setStrokeColor(
        colors.HexColor("#b71c1c")
    )

    p.line(
        145,
        507,
        width - 145,
        507
    )

    # =====================================
    # APPRECIATION MESSAGE
    # =====================================

    p.setFillColor(
        colors.HexColor("#263238")
    )

    p.setFont(
        "Helvetica",
        12
    )

    p.drawCentredString(
        width / 2,
        475,
        "in sincere appreciation for voluntarily donating blood"
    )

    p.drawCentredString(
        width / 2,
        453,
        "and helping save precious lives."
    )

    # =====================================
    # THANK YOU
    # =====================================

    p.setFillColor(
        colors.HexColor("#9e0000")
    )

    p.setFont(
        "Helvetica-Oblique",
        16
    )

    p.drawCentredString(
        width / 2,
        415,
        "Your kindness is a gift of life."
    )

    p.setFont(
        "Helvetica-Bold",
        14
    )

    p.drawCentredString(
        width / 2,
        390,
        "♥  Thank You!  ♥"
    )

    # =====================================
    # DONOR DETAILS BOX
    # =====================================

    box_x = 75
    box_y = 205
    box_width = 315
    box_height = 145

    p.setStrokeColor(
        colors.HexColor("#b71c1c")
    )

    p.setLineWidth(1.5)

    p.roundRect(
        box_x,
        box_y,
        box_width,
        box_height,
        10,
        fill=0,
        stroke=1
    )

    # Blood Group
    p.setFillColor(
        colors.HexColor("#263238")
    )

    p.setFont(
        "Helvetica-Bold",
        11
    )

    p.drawString(
        box_x + 18,
        box_y + 112,
        "Blood Group"
    )

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        box_x + 140,
        box_y + 112,
        f": {donor.blood_group}"
    )

    # City
    p.setFont(
        "Helvetica-Bold",
        11
    )

    p.drawString(
        box_x + 18,
        box_y + 84,
        "City"
    )

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        box_x + 140,
        box_y + 84,
        f": {donor.city}"
    )

    # Date
    p.setFont(
        "Helvetica-Bold",
        11
    )

    p.drawString(
        box_x + 18,
        box_y + 56,
        "Date"
    )

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        box_x + 140,
        box_y + 56,
        f": {datetime.now().strftime('%d-%m-%Y')}"
    )

    # Donor ID
    p.setFont(
        "Helvetica-Bold",
        11
    )

    p.drawString(
        box_x + 18,
        box_y + 28,
        "Donor ID"
    )

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        box_x + 140,
        box_y + 28,
        f": BLK{donor.id:05d}"
    )

    # =====================================
    # BLOOD DONOR HERO BADGE
    # =====================================

    badge_x = 475
    badge_y = 275

    p.setFillColor(
        colors.HexColor("#b71c1c")
    )

    p.circle(
        badge_x,
        badge_y,
        58,
        fill=1,
        stroke=0
    )

    p.setStrokeColor(colors.white)

    p.setLineWidth(2)

    p.circle(
        badge_x,
        badge_y,
        45,
        fill=0,
        stroke=1
    )

    # Plus sign
    p.setFillColor(colors.white)

    p.rect(
        badge_x - 4,
        badge_y - 18,
        8,
        36,
        fill=1,
        stroke=0
    )

    p.rect(
        badge_x - 18,
        badge_y - 4,
        36,
        8,
        fill=1,
        stroke=0
    )

    p.setFont(
        "Helvetica-Bold",
        8
    )

    p.drawCentredString(
        badge_x,
        badge_y - 31,
        "BLOOD DONOR"
    )

    p.drawCentredString(
        badge_x,
        badge_y - 42,
        "HERO"
    )

    # =====================================
    # SIGNATURE
    # =====================================

    p.setFillColor(
        colors.HexColor("#263238")
    )

    p.setFont(
        "Helvetica-Oblique",
        17
    )

    p.drawCentredString(
        470,
        155,
        "BloodLink Team"
    )

    p.setStrokeColor(
        colors.HexColor("#263238")
    )

    p.line(
        400,
        142,
        540,
        142
    )

    p.setFont(
        "Helvetica",
        9
    )

    p.drawCentredString(
        470,
        127,
        "Authorized Signature"
    )

    p.drawCentredString(
        470,
        113,
        "BloodLink Team"
    )

    # =====================================
    # BOTTOM MESSAGE
    # =====================================

    p.setFillColor(
        colors.HexColor("#9e0000")
    )

    p.setFont(
        "Helvetica-Oblique",
        10
    )

    p.drawCentredString(
        width / 2,
        70,
        "Every drop you donate creates a ripple of hope."
    )

    # =====================================
    # FINISH PDF
    # =====================================

    p.showPage()
    p.save()

    return response