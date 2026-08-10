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
from django.conf import settings
import os
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
    EmergencyRequestForm,
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
# Register View
# Register View

# Register View

def register(request):

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "Registration successful! Please login."
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
    
# Login View

class UserLoginView(LoginView):

    template_name = "accounts/login.html"

# Dashboard

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
def download_pdf(request, id):

    donor = UserProfile.objects.filter(id=id).first()

    if donor is None:
        return HttpResponse("Donor not found.")

    if donor.donation_count < 1:
        return HttpResponse(
            "Certificate is available after at least one blood donation."
        )

    # -----------------------------
    # PDF RESPONSE
    # -----------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="BloodLink_Certificate.pdf"'
    )

    # A4 size
    width, height = A4

    p = canvas.Canvas(
        response,
        pagesize=A4
    )

    # -----------------------------
    # COLORS
    # -----------------------------

    red = colors.HexColor("#9E3F43")
    gold = colors.HexColor("#B99A5B")
    dark = colors.HexColor("#252B35")
    light_red = colors.HexColor("#C88A8D")

    # -----------------------------
    # OUTER BORDER
    # -----------------------------

    p.setStrokeColor(red)
    p.setLineWidth(5)

    p.rect(
        28,
        28,
        width - 56,
        height - 56
    )

    # -----------------------------
    # INNER BORDER
    # -----------------------------

    p.setStrokeColor(gold)
    p.setLineWidth(1)

    p.rect(
        39,
        39,
        width - 78,
        height - 78
    )

    # -----------------------------
    # INNER LIGHT BORDER
    # -----------------------------

    p.setStrokeColor(colors.HexColor("#D8D8D8"))
    p.setLineWidth(0.6)

    p.rect(
        47,
        47,
        width - 94,
        height - 94
    )

    # -----------------------------
    # BLOODLINK
    # -----------------------------

    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 24)

    p.drawCentredString(
        width / 2,
        height - 95,
        "BloodLink"
    )

    p.setFillColor(dark)
    p.setFont("Helvetica-Bold", 8)

    p.drawCentredString(
        width / 2,
        height - 116,
        "SAVE BLOOD • SAVE LIFE"
    )

    # Gold separator
    p.setStrokeColor(gold)
    p.setLineWidth(1)

    p.line(
        150,
        height - 135,
        width - 150,
        height - 135
    )

    # -----------------------------
    # CERTIFICATE TITLE
    # -----------------------------

    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 29)

    p.drawCentredString(
        width / 2,
        height - 185,
        "CERTIFICATE"
    )

    p.setFillColor(dark)
    p.setFont("Helvetica-Bold", 18)

    p.drawCentredString(
        width / 2,
        height - 212,
        "OF APPRECIATION"
    )

    p.setStrokeColor(gold)
    p.setLineWidth(1)

    p.line(
        165,
        height - 230,
        width - 165,
        height - 230
    )

    # -----------------------------
    # PRESENTED TO
    # -----------------------------

    p.setFillColor(dark)
    p.setFont("Helvetica", 11)

    p.drawCentredString(
        width / 2,
        height - 270,
        "This certificate is proudly presented to"
    )

    # Donor Name
    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 23)

    p.drawCentredString(
        width / 2,
        height - 305,
        donor.full_name
    )

    # Name underline
    p.setStrokeColor(gold)
    p.setLineWidth(1)

    p.line(
        150,
        height - 317,
        width - 150,
        height - 317
    )

    # -----------------------------
    # APPRECIATION MESSAGE
    # -----------------------------

    p.setFillColor(dark)
    p.setFont("Helvetica", 10.5)

    p.drawCentredString(
        width / 2,
        height - 350,
        "in sincere appreciation for voluntarily donating blood"
    )

    p.drawCentredString(
        width / 2,
        height - 368,
        "and making a meaningful contribution toward saving lives."
    )

    # -----------------------------
    # DONOR INFORMATION BOX
    # -----------------------------

    box_x = 80
    box_y = height - 535
    box_w = 280
    box_h = 125

    p.setStrokeColor(light_red)
    p.setLineWidth(1.2)

    p.roundRect(
        box_x,
        box_y,
        box_w,
        box_h,
        12
    )

    # Heading
    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 11)

    p.drawString(
        box_x + 18,
        box_y + box_h - 25,
        "DONOR INFORMATION"
    )

    # Heading line
    p.setStrokeColor(gold)
    p.setLineWidth(1)

    p.line(
        box_x + 18,
        box_y + box_h - 35,
        box_x + box_w - 18,
        box_y + box_h - 35
    )

    # Information
    p.setFillColor(dark)
    p.setFont("Helvetica-Bold", 9.5)

    p.drawString(box_x + 18, box_y + 72, "Blood Group")
    p.drawString(box_x + 18, box_y + 48, "City")
    p.drawString(box_x + 18, box_y + 24, "Donation Count")

    p.setFont("Helvetica", 9.5)

    p.drawString(
        box_x + 125,
        box_y + 72,
        f":  {donor.blood_group}"
    )

    p.drawString(
        box_x + 125,
        box_y + 48,
        f":  {donor.city}"
    )

    p.drawString(
        box_x + 125,
        box_y + 24,
        f":  {donor.donation_count}"
    )

    # -----------------------------
    # BLOOD GROUP CIRCLE
    # -----------------------------

    circle_x = width - 135
    circle_y = height - 465
    radius = 43

    p.setStrokeColor(red)
    p.setLineWidth(3)

    p.circle(
        circle_x,
        circle_y,
        radius
    )

    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 22)

    p.drawCentredString(
        circle_x,
        circle_y + 5,
        donor.blood_group
    )

    p.setFillColor(dark)
    p.setFont("Helvetica-Bold", 5.5)

    p.drawCentredString(
        circle_x,
        circle_y - 15,
        "BLOOD GROUP"
    )

    # -----------------------------
    # VERIFIED BADGE
    # -----------------------------

    badge_y = circle_y - 78
    badge_radius = 34

    p.setStrokeColor(gold)
    p.setLineWidth(2)

    p.circle(
        circle_x,
        badge_y,
        badge_radius
    )

    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 6.5)

    p.drawCentredString(
        circle_x,
        badge_y + 7,
        "VERIFIED"
    )

    p.drawCentredString(
        circle_x,
        badge_y - 3,
        "BLOODLINK"
    )

    p.setFillColor(dark)
    p.setFont("Helvetica-Bold", 5.5)

    p.drawCentredString(
        circle_x,
        badge_y - 14,
        "DONOR"
    )

    # Donor ID
    donor_id = f"BLK{donor.id:06d}"

    p.setFillColor(dark)
    p.setFont("Helvetica", 7)

    p.drawCentredString(
        circle_x,
        badge_y - 58,
        f"Donor ID: {donor_id}"
    )

    # -----------------------------
    # DONATION DATE
    # -----------------------------

    today = datetime.now()

    date_text = today.strftime("%d %B %Y")

    p.setFillColor(dark)
    p.setFont("Helvetica-Bold", 9)

    p.drawString(
        90,
        height - 575,
        "DONATION DATE"
    )

    p.setFont("Helvetica", 9)

    p.drawString(
        90,
        height - 592,
        date_text
    )

    # -----------------------------
    # CERTIFICATE ID
    # -----------------------------

    certificate_id = f"BL-CERT-{donor.id:06d}"

    p.setFont("Helvetica-Bold", 9)

    p.drawString(
        90,
        height - 630,
        "CERTIFICATE ID"
    )

    p.setFont("Helvetica", 9)

    p.drawString(
        90,
        height - 647,
        certificate_id
    )

    # -----------------------------
    # SIGNATURE
    # -----------------------------

    signature_x = width - 155

    p.setFillColor(dark)
    p.setFont("Helvetica-Oblique", 16)

    p.drawCentredString(
        signature_x,
        height - 620,
        "BloodLink Team"
    )

    p.setStrokeColor(red)
    p.setLineWidth(1.5)

    p.line(
        signature_x - 70,
        height - 630,
        signature_x + 70,
        height - 630
    )

    p.setFillColor(dark)
    p.setFont("Helvetica", 6.5)

    p.drawCentredString(
        signature_x,
        height - 645,
        "AUTHORIZED SIGNATURE"
    )

    # -----------------------------
    # FOOTER
    # -----------------------------

    p.setFillColor(red)
    p.setFont("Helvetica-Bold", 9)

    p.drawCentredString(
        width / 2,
        92,
        "EVERY DROP COUNTS. EVERY DONOR MATTERS."
    )

    p.setFillColor(dark)
    p.setFont("Helvetica", 6.5)

    p.drawCentredString(
        width / 2,
        75,
        "Issued by BloodLink • Saving lives through voluntary blood donation"
    )

    # -----------------------------
    # SAVE PDF
    # -----------------------------

    p.showPage()
    p.save()

    return response

@login_required
def emergency_request(request):

    if request.method == "POST":

        form = EmergencyRequestForm(request.POST)

        if form.is_valid():

            emergency = form.save()

            messages.success(
                request,
                "Emergency request submitted successfully!"
            )

            return redirect("/dashboard/")

    else:

        form = EmergencyRequestForm()

    return render(
        request,
        "accounts/emergency_request.html",
        {
            "form": form
        }
    )