from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import UserProfile, BloodRequest
from .forms import RegistrationForm, UserProfileForm, BloodRequestForm
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import datetime
from reportlab.platypus import Image
import os

import requests
from django.http import JsonResponse
from .models import OTPVerification
from .utils import generate_otp



def home(request):

    total_donors = UserProfile.objects.count()

    total_requests = BloodRequest.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    recent_requests = BloodRequest.objects.all().order_by("-id")[:5]
    return render(request, "home.html", {
    "total_donors": total_donors,
    "total_requests": total_requests,
    "available_donors": available_donors,
    "recent_requests": recent_requests,
})


class UserLoginView(LoginView):
    template_name = "accounts/login.html"


@login_required
def dashboard(request):
    total_donors = UserProfile.objects.count()
    total_requests = BloodRequest.objects.count()
    available_donors = UserProfile.objects.filter(is_available=True).count()

    blood_stats = UserProfile.objects.values("blood_group").annotate(total=Count("id"))

    latest_donors = UserProfile.objects.order_by("-id")[:5]
    recent_requests = BloodRequest.objects.order_by("-id")[:5]

    return render(request, "accounts/dashboard.html", {
        "total_donors": total_donors,
        "total_requests": total_requests,
        "available_donors": available_donors,
        "blood_stats": blood_stats,
        "latest_donors": latest_donors,
        "recent_requests": recent_requests,
    })


def user_logout(request):
    logout(request)
    return redirect("/login/")


@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect("/profile/")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "accounts/profile.html", {
        "form": form
    })
@login_required
def donor_list(request):
    donors = UserProfile.objects.all()

    blood_group = request.GET.get("blood_group")
    city = request.GET.get("city")

    if blood_group:
        donors = donors.filter(blood_group=blood_group)

    if city:
        donors = donors.filter(city__icontains=city)

    return render(request, "accounts/donor_list.html", {
        "donors": donors
    })


@login_required
def donor_detail(request, id):
    donor = UserProfile.objects.get(id=id)

    return render(request, "accounts/donor_detail.html", {
        "donor": donor
    })


@login_required
def request_blood(request):
    if request.method == "POST":
        form = BloodRequestForm(request.POST)

        if form.is_valid():
            blood_request = form.save()

            # Matching donors चे email घ्या
            emails = UserProfile.objects.filter(
                blood_group=blood_request.blood_group,
                city=blood_request.city,      # City पण match होईल
                is_available=True
            ).exclude(
                user__email=""
            ).values_list(
                "user__email", flat=True
            )

            # Matching donors ना email पाठवा
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

    else:
        form = BloodRequestForm()

    return render(request, "accounts/request_blood.html", {
        "form": form
    })

    messages.success(request, "Blood request submitted successfully!")
    return redirect("/dashboard/")


@login_required
def blood_request_list(request):
    requests = BloodRequest.objects.all()

    return render(request, "accounts/blood_request_list.html", {
        "requests": requests
    })


@login_required
def matching_donors(request, id):
    blood_request = BloodRequest.objects.get(id=id)

    donors = UserProfile.objects.filter(
        blood_group=blood_request.blood_group,
        city=blood_request.city
    )

    return render(request, "accounts/matching_donors.html", {
        "blood_request": blood_request,
        "donors": donors
    })


def about(request):
    return render(request, "accounts/about.html")


def contact(request):
    return render(request, "accounts/contact.html")


from reportlab.pdfgen import canvas

@login_required
def download_pdf(request):

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="BloodLink_Report.pdf"'

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    story = []

    donor_data = [
        ["Name", "Blood Group", "City"]
    ]

    

    # ---------------- Logo ----------------

    logo_path = os.path.join(settings.MEDIA_ROOT, "logo.png")
    print("LOGO PATH:", logo_path)
    print("LOGO EXISTS:", os.path.exists(logo_path))

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=80, height=80)
        story.append(logo)


    # ---------------- Title ----------------

    title = styles["Heading1"]
    title.alignment = TA_CENTER

    story.append(
        Paragraph("🩸 BloodLink Report", title)
    )

    story.append(
        Paragraph("<br/><br/>", styles["Normal"])
    )


    # ---------------- Statistics ----------------

    total_donors = UserProfile.objects.count()

    total_requests = BloodRequest.objects.count()

    available = UserProfile.objects.filter(
        is_available=True
    ).count()


    stats = [
        ["Statistics", "Count"],
        ["Total Donors", str(total_donors)],
        ["Blood Requests", str(total_requests)],
        ["Available Donors", str(available)],
    ]


    stats_table = Table(stats)

    stats_table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.red),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

    ]))
    current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    story.append(
        Paragraph(
            "Generated On : " + current_time,
            styles["Normal"]
        )
    )


    # ---------------- Donor Table ----------------

    donor_data = [
        ["Name", "Blood Group", "City"]
    ]

    for donor in UserProfile.objects.all():

        donor_data.append([
            donor.user.get_full_name(),
            donor.blood_group,
            donor.city
        ])


    donor_table = Table(donor_data)


    donor_table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.darkgreen),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

    ]))


    story.append(
        Paragraph("Donor List", styles["Heading2"])
    )

    story.append(donor_table)


    story.append(
        Paragraph("<br/><br/>", styles["Normal"])
    )


    # ---------------- Blood Request Table ----------------

    request_data = [
        ["Patient", "Blood", "City", "Units"]
    ]


    for req in BloodRequest.objects.all():

        request_data.append([

            req.patient_name,

            req.blood_group,

            req.city,

            str(req.units_required)

        ])



    request_table = Table(request_data)


    request_table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.darkred),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

    ]))


    story.append(
        Paragraph("Blood Requests", styles["Heading2"])
    )

    story.append(request_table)



    # ---------------- Build PDF ----------------

    doc.build(story)


    return response



def send_otp(request):

    mobile = request.POST.get("mobile")

    otp = generate_otp()

    OTPVerification.objects.create(
        mobile=mobile,
        otp=otp
    )

    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "route": "otp",
        "variables_values": otp,
        "numbers": mobile,
    }

    headers = {
        "authorization": "CBg6dNL7KQOp0DtmzjwlTRvPxJFuA5cW489ibqsh1UnSekHG3Mrq2xg1eR6wuNvYX9i5QHakGAzfIF0y",
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers
    )

    print(response.text)

    return JsonResponse({
        "message": "OTP Sent Successfully"
    })
    

def verify_otp(request):
    mobile = request.POST.get("mobile")
    otp = request.POST.get("otp")

    result = OTPVerification.objects.filter(
        mobile=mobile,
        otp=otp,
        is_verified=False
    ).last()

    if result:
        result.is_verified = True
        result.save()

        return JsonResponse({
            "message": "OTP Verified"
        })

    return JsonResponse({
        "message": "Invalid OTP"
    })