from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


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

# ---------------- Donation Certificate ----------------

@login_required
def donation_certificate(request, id):

    donor = UserProfile.objects.get(id=id)

    # Certificate फक्त donation केल्यानंतर
    if donor.donation_count == 0:
        messages.error(
            request,
            "Certificate is available only after completing a blood donation."
        )
        return redirect("/donors/")

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Donation_Certificate.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)

    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(
        300,
        780,
        "Blood Donation Certificate"
    )

    p.setFont("Helvetica", 16)

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
        f"Date: {datetime.now().strftime('%d-%m-%Y')}"
    )

    p.setFont("Helvetica-Bold", 14)

    p.drawCentredString(
        300,
        570,
        "Thank You For Saving A Life!"
    )

    p.showPage()
    p.save()

    return response

@login_required
def download_pdf(request):

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="BloodLink_Report.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    story = []

    # ---------------- Title ----------------

    title = styles["Heading1"]
    title.alignment = TA_CENTER

    story.append(
        Paragraph(
            "BloodLink Report",
            title
        )
    )

    # ---------------- Date ----------------

    story.append(
        Paragraph(
            "Generated On: " +
            datetime.now().strftime(
                "%d-%m-%Y %I:%M:%S %p"
            ),
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "<br/><br/>",
            styles["Normal"]
        )
    )

    # ---------------- Statistics ----------------

    total_donors = UserProfile.objects.count()

    total_requests = BloodRequest.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    stats = [
        ["Statistics", "Count"],
        ["Total Donors", total_donors],
        ["Blood Requests", total_requests],
        ["Available Donors", available_donors],
    ]

    stats_table = Table(stats)

    stats_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.red),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )

    story.append(stats_table)

    story.append(
        Paragraph(
            "<br/><br/>",
            styles["Normal"]
        )
    )

    # ---------------- Donor List ----------------

    story.append(
        Paragraph(
            "Donor List",
            styles["Heading2"]
        )
    )

    donor_data = [
        ["Name", "Blood Group", "City"]
    ]

    for donor in UserProfile.objects.all():

        donor_data.append([
            donor.full_name,
            donor.blood_group,
            donor.city,
        ])

    donor_table = Table(donor_data)

    donor_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )

    story.append(donor_table)

    story.append(
        Paragraph(
            "<br/><br/>",
            styles["Normal"]
        )
    )

    # ---------------- Blood Requests ----------------

    story.append(
        Paragraph(
            "Blood Requests",
            styles["Heading2"]
        )
    )

    request_data = [
        ["Patient", "Blood", "City", "Units"]
    ]

    for req in BloodRequest.objects.all():

        request_data.append([
            req.patient_name,
            req.blood_group,
            req.city,
            str(req.units_required),
        ])

    request_table = Table(request_data)

    request_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )

    story.append(request_table)

    # ---------------- Generate PDF ----------------

    doc.build(story)

    return response