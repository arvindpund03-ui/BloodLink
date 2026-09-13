from io import BytesIO
from uuid import uuid4
from datetime import timedelta

import qrcode

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .firebase import send_admin_emergency_notification

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

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                user = form.save()

                profile, created = UserProfile.objects.get_or_create(
                    user=user
                )

                profile.full_name = form.cleaned_data.get(
                    "full_name",
                    ""
                )

                profile.blood_group = form.cleaned_data.get(
                    "blood_group",
                    ""
                )

                profile.phone = form.cleaned_data.get(
                    "phone",
                    ""
                )

                profile.city = form.cleaned_data.get(
                    "city",
                    ""
                )

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
        {
            "form": form
        }
    )


# =========================================================
# LOGIN
# =========================================================

class UserLoginView(FormView):

    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("dashboard")

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def form_valid(self, form):

        login(
            self.request,
            form.get_user()
        )

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

@require_POST
@login_required
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

@login_required
def dashboard(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    # -----------------------------------------------------
    # DONOR STATISTICS
    # -----------------------------------------------------

    total_donors = UserProfile.objects.count()

    available_donors = UserProfile.objects.filter(
        is_available=True
    ).count()

    recent_donors = (
        UserProfile.objects
        .select_related("user")
        .order_by("-id")[:5]
    )

    # -----------------------------------------------------
    # BLOOD REQUEST STATISTICS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # BLOOD GROUP STATISTICS
    # -----------------------------------------------------

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

        blood_group_stats.append(
            {
                "group": group,
                "count": total,
                "available": available,
            }
        )

    # -----------------------------------------------------
    # DONATION STATISTICS
    # -----------------------------------------------------

    lives_saved = DonationCertificate.objects.count()

    # -----------------------------------------------------
    # ACTIVE EMERGENCIES
    # -----------------------------------------------------

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
# ACTIVE EMERGENCY LIST
# =========================================================

@login_required
def active_emergency_list(request):

    emergencies = (
        EmergencyRequest.objects
        .filter(status="ACTIVE")
        .order_by("-created_at")
    )

    return render(
        request,
        "accounts/active_emergency_list.html",
        {
            "emergencies": emergencies
        }
    )


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):

    profile_obj, created = UserProfile.objects.get_or_create(
        user=request.user
    )

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

        form = UserProfileForm(
            instance=profile_obj
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form
        }
    )


# =========================================================
# DONOR DIRECTORY
# =========================================================

def donor_list(request):

    donors = (
        UserProfile.objects
        .select_related("user")
        .filter(is_available=True)
        .order_by("blood_group", "full_name")
    )

    blood_group = request.GET.get(
        "blood_group",
        ""
    ).strip()

    city = request.GET.get(
        "city",
        ""
    ).strip()

    search = request.GET.get(
        "search",
        ""
    ).strip()

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

        id=id,

        is_available=True
    )

    return render(
        request,
        "accounts/donor_detail.html",
        {
            "donor": donor
        }
    )


# =========================================================
# REQUEST BLOOD
# =========================================================

@login_required
def request_blood(request):

    if request.method == "POST":

        form = BloodRequestForm(request.POST)

        if form.is_valid():

            blood_request = form.save(
                commit=False
            )

            # जर BloodRequest model मध्ये user field असेल
            # तर uncomment करा:
            #
            # blood_request.user = request.user

            blood_request.save()

            messages.success(
                request,
                "Blood request submitted successfully!"
            )

            return redirect("blood_request_list")

    else:

        form = BloodRequestForm()

    return render(
        request,
        "accounts/request_blood.html",
        {
            "form": form
        }
    )


# =========================================================
# BLOOD REQUEST LIST
# =========================================================

@login_required
def blood_request_list(request):

    blood_requests = (
        BloodRequest.objects
        .all()
        .order_by("-id")
    )

    pending_requests = blood_requests.filter(
        status="Pending"
    ).count()

    fulfilled_requests = blood_requests.filter(
        status="Fulfilled"
    ).count()

    context = {

        "requests": blood_requests,

        "pending_requests": pending_requests,

        "fulfilled_requests": fulfilled_requests,

    }

    return render(
        request,
        "accounts/blood_request_list.html",
        context
    )


# =========================================================
# MATCHING DONORS
# =========================================================

@login_required
def matching_donors(request, id):

    blood_request = get_object_or_404(
        BloodRequest,
        id=id
    )

    donors = (
        UserProfile.objects
        .select_related("user")
        .filter(
            blood_group=blood_request.blood_group,
            is_available=True
        )
    )

    # Prefer donors from same city

    if blood_request.city:

        city_donors = donors.filter(
            city__icontains=blood_request.city
        )

        if city_donors.exists():

            donors = city_donors

    donors = donors.order_by(
        "city",
        "full_name"
    )

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

@login_required
def emergency_request(request):

    if request.method == "POST":

        form = EmergencyRequestForm(
            request.POST
        )

        if form.is_valid():

            # -------------------------------------------------
            # CLEAN DATA
            # -------------------------------------------------

            patient_name = form.cleaned_data[
                "patient_name"
            ].strip()

            blood_group = form.cleaned_data[
                "blood_group"
            ].strip()

            hospital_name = form.cleaned_data[
                "hospital_name"
            ].strip()

            city = form.cleaned_data[
                "city"
            ].strip()

            contact_number = form.cleaned_data[
                "contact_number"
            ].strip()

            units_required = form.cleaned_data[
                "units_required"
            ]

            emergency_type = form.cleaned_data[
                "emergency_type"
            ]

            # -------------------------------------------------
            # EXACT DUPLICATE CHECK
            # -------------------------------------------------

            exact_duplicate = (
                EmergencyRequest.objects
                .filter(

                    status="ACTIVE",

                    patient_name__iexact=patient_name,

                    blood_group=blood_group,

                    hospital_name__iexact=hospital_name,

                    city__iexact=city,

                    contact_number=contact_number,

                    units_required=units_required,

                    emergency_type=emergency_type,

                )
                .order_by("-created_at")
                .first()
            )

            if exact_duplicate:

                messages.warning(
                    request,
                    "This emergency request is already active."
                )

                return redirect(
                    "emergency_request"
                )

            # -------------------------------------------------
            # 15 MINUTE COOLDOWN
            # -------------------------------------------------

            cooldown_time = (
                timezone.now()
                - timedelta(minutes=15)
            )

            recent_duplicate = (
                EmergencyRequest.objects
                .filter(

                    created_at__gte=cooldown_time,

                    status__in=[
                        "ACTIVE",
                        "MATCHED"
                    ],

                    patient_name__iexact=patient_name,

                    hospital_name__iexact=hospital_name,

                    city__iexact=city,

                    contact_number=contact_number,

                )
                .order_by("-created_at")
                .first()
            )

            if recent_duplicate:

                messages.warning(
                    request,
                    "A similar emergency request was submitted recently. "
                    "Please wait before submitting it again."
                )

                return redirect(
                    "emergency_request"
                )

            # -------------------------------------------------
            # CREATE EMERGENCY
            # -------------------------------------------------

            with transaction.atomic():

                emergency = form.save(
                    commit=False
                )
                emergency.created_by = request.user

                emergency.patient_name = patient_name
                emergency.blood_group = blood_group
                emergency.hospital_name = hospital_name
                emergency.city = city
                emergency.contact_number = contact_number
                emergency.units_required = units_required
                emergency.emergency_type = emergency_type

                emergency.status = "ACTIVE"

                emergency.save()

            # -------------------------------------------------
            # SEND ADMIN NOTIFICATION
            # -------------------------------------------------

            try:

                send_admin_emergency_notification(
                    emergency
                )

            except Exception:

                # Notification failure should not stop
                # emergency request creation
                pass

            messages.success(
                request,
                "Emergency request submitted successfully. "
                "The emergency support team has been notified."
            )

            return redirect(
                "emergency_request"
            )

    else:

        form = EmergencyRequestForm()

    return render(
        request,
        "accounts/emergency_request.html",
        {
            "form": form
        }
    )


# =========================================================
# DOWNLOAD DONATION CERTIFICATE PDF
# =========================================================

@login_required
def download_pdf(request, id):

    donor = get_object_or_404(
        UserProfile.objects.select_related("user"),
        id=id
    )

    issue_date = timezone.localdate()

    # -----------------------------------------------------
    # GET OR CREATE CERTIFICATE
    # -----------------------------------------------------

    certificate = (
        DonationCertificate.objects
        .filter(donor=donor)
        .order_by("-id")
        .first()
    )

    if certificate is None:

        certificate = DonationCertificate.objects.create(

            donor=donor,

            donation_date=issue_date,

            certificate_number=(
                f"BL-{donor.id}-"
                f"{uuid4().hex[:8].upper()}"
            )

        )

    certificate_number = certificate.certificate_number

    # -----------------------------------------------------
    # DONOR ID
    # -----------------------------------------------------

    donor_id = (
        f"BLK{issue_date.strftime('%Y%m%d')}"
        f"{donor.id:04d}"
    )

    # -----------------------------------------------------
    # VERIFICATION URL
    # -----------------------------------------------------

    verification_url = request.build_absolute_uri(
        f"/verify-certificate/{certificate_number}/"
    )

    # -----------------------------------------------------
    # QR CODE
    # -----------------------------------------------------

    qr = qrcode.QRCode(

        version=1,

        error_correction=qrcode.constants.ERROR_CORRECT_H,

        box_size=8,

        border=3,

    )

    qr.add_data(verification_url)

    qr.make(fit=True)

    qr_image = qr.make_image(

        fill_color="#111827",

        back_color="white"

    )

    qr_buffer = BytesIO()

    qr_image.save(
        qr_buffer,
        format="PNG"
    )

    qr_buffer.seek(0)

    # -----------------------------------------------------
    # PDF SETUP
    # -----------------------------------------------------

    buffer = BytesIO()

    page_width, page_height = landscape(A4)

    pdf = canvas.Canvas(
        buffer,
        pagesize=landscape(A4)
    )

    # -----------------------------------------------------
    # COLORS
    # -----------------------------------------------------

    PURPLE = colors.HexColor("#6D28D9")
    DARK_PURPLE = colors.HexColor("#4C1D95")
    BLUE = colors.HexColor("#2563EB")
    CORAL = colors.HexColor("#F43F5E")
    GOLD = colors.HexColor("#F59E0B")
    NAVY = colors.HexColor("#111827")
    DARK = colors.HexColor("#1F2937")
    MUTED = colors.HexColor("#64748B")
    WHITE = colors.white
    LIGHT = colors.HexColor("#F8FAFC")
    BORDER = colors.HexColor("#CBD5E1")
    GREEN = colors.HexColor("#15803D")
    LIGHT_GOLD = colors.HexColor("#FEF3C7")

    # -----------------------------------------------------
    # BACKGROUND
    # -----------------------------------------------------

    pdf.setFillColor(WHITE)

    pdf.rect(
        0,
        0,
        page_width,
        page_height,
        fill=1,
        stroke=0
    )

    # -----------------------------------------------------
    # OUTER BORDER
    # -----------------------------------------------------

    pdf.setStrokeColor(PURPLE)
    pdf.setLineWidth(6)

    pdf.roundRect(
        15,
        15,
        page_width - 30,
        page_height - 30,
        18,
        fill=0,
        stroke=1
    )

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(2)

    pdf.roundRect(
        27,
        27,
        page_width - 54,
        page_height - 54,
        13,
        fill=0,
        stroke=1
    )

    # -----------------------------------------------------
    # TOP BRAND BARS
    # -----------------------------------------------------

    for color, y in [

        (PURPLE, page_height - 38),
        (BLUE, page_height - 43),
        (CORAL, page_height - 48),

    ]:

        pdf.setFillColor(color)

        pdf.rect(
            30,
            y,
            page_width - 60,
            5,
            fill=1,
            stroke=0
        )

    # -----------------------------------------------------
    # WATERMARK
    # -----------------------------------------------------

    pdf.saveState()

    pdf.setFillColor(
        colors.HexColor("#F3F4F6")
    )

    pdf.setFont(
        "Helvetica-Bold",
        70
    )

    pdf.translate(
        page_width / 2,
        page_height / 2
    )

    pdf.rotate(22)

    pdf.drawCentredString(
        0,
        0,
        "BLOODLINK"
    )

    pdf.restoreState()

    # -----------------------------------------------------
    # LOGO
    # -----------------------------------------------------

    logo_x = 72
    logo_y = page_height - 83

    pdf.setFillColor(PURPLE)

    pdf.circle(
        logo_x,
        logo_y,
        28,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(BLUE)

    pdf.circle(
        logo_x,
        logo_y,
        22,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(CORAL)

    path = pdf.beginPath()

    path.moveTo(
        logo_x,
        logo_y + 15
    )

    path.curveTo(
        logo_x - 13,
        logo_y - 2,
        logo_x - 10,
        logo_y - 12,
        logo_x,
        logo_y - 15
    )

    path.curveTo(
        logo_x + 10,
        logo_y - 12,
        logo_x + 13,
        logo_y - 2,
        logo_x,
        logo_y + 15
    )

    pdf.drawPath(
        path,
        fill=1,
        stroke=0
    )

    # -----------------------------------------------------
    # BRAND NAME
    # -----------------------------------------------------

    pdf.setFillColor(NAVY)

    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawString(
        110,
        page_height - 67,
        "BloodLink"
    )

    pdf.setFillColor(PURPLE)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        111,
        page_height - 81,
        "BLOOD DONATION & EMERGENCY SUPPORT NETWORK"
    )

    # -----------------------------------------------------
    # OFFICIAL BADGE
    # -----------------------------------------------------

    badge_x = page_width - 185
    badge_y = page_height - 75

    pdf.setFillColor(LIGHT_GOLD)

    pdf.roundRect(
        badge_x,
        badge_y - 17,
        125,
        32,
        16,
        fill=1,
        stroke=0
    )

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1)

    pdf.roundRect(
        badge_x,
        badge_y - 17,
        125,
        32,
        16,
        fill=0,
        stroke=1
    )

    pdf.setFillColor(DARK)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawCentredString(
        badge_x + 62.5,
        badge_y - 5,
        "OFFICIAL CERTIFICATE"
    )

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title_y = page_height - 153

    pdf.setFillColor(BLUE)

    pdf.setFont(
        "Helvetica-Bold",
        9
    )

    pdf.drawCentredString(
        page_width / 2,
        title_y + 13,
        "DONOR RECOGNITION & EMERGENCY SUPPORT"
    )

    pdf.setFillColor(NAVY)

    pdf.setFont(
        "Helvetica-Bold",
        27
    )

    pdf.drawCentredString(
        page_width / 2,
        title_y - 15,
        "CERTIFICATE OF APPRECIATION"
    )

    pdf.setFillColor(MUTED)

    pdf.setFont(
        "Helvetica-Oblique",
        9.5
    )

    pdf.drawCentredString(
        page_width / 2,
        title_y - 35,
        "Recognizing compassion, humanity and commitment to saving lives"
    )

    # -----------------------------------------------------
    # PRESENTED TO
    # -----------------------------------------------------

    pdf.setFillColor(CORAL)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawCentredString(
        page_width / 2,
        title_y - 61,
        "THIS CERTIFICATE IS PROUDLY PRESENTED TO"
    )

    # -----------------------------------------------------
    # DONOR NAME
    # -----------------------------------------------------

    donor_name = (
        donor.full_name
        or donor.user.get_full_name()
        or donor.user.username
    )

    donor_name = donor_name.upper()

    pdf.setFillColor(DARK_PURPLE)

    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawCentredString(
        page_width / 2,
        title_y - 91,
        donor_name
    )

    name_width = pdf.stringWidth(
        donor_name,
        "Helvetica-Bold",
        24
    )

    pdf.setStrokeColor(CORAL)
    pdf.setLineWidth(2)

    pdf.line(
        (page_width - name_width) / 2,
        title_y - 99,
        (page_width + name_width) / 2,
        title_y - 99
    )

    # -----------------------------------------------------
    # APPRECIATION MESSAGE
    # -----------------------------------------------------

    pdf.setFillColor(DARK)

    pdf.setFont(
        "Helvetica",
        9
    )

    message_lines = [

        "in sincere appreciation for your valuable contribution",

        "towards blood donation and emergency support,",

        "helping patients, accident victims and families receive timely assistance.",

    ]

    message_y = title_y - 121

    for line in message_lines:

        pdf.drawCentredString(
            page_width / 2,
            message_y,
            line
        )

        message_y -= 12

    pdf.setFillColor(CORAL)

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawCentredString(
        page_width / 2,
        message_y - 4,
        "YOUR KINDNESS CAN SAVE A LIFE"
    )

    # -----------------------------------------------------
    # INFORMATION CARDS
    # -----------------------------------------------------

    cards_y = 105
    card_height = 50
    card_width = 116
    gap = 12

    total_width = (
        card_width * 4
        + gap * 3
    )

    start_x = (
        page_width - total_width
    ) / 2

    details = [

        (
            "BLOOD GROUP",
            donor.blood_group or "N/A",
            CORAL
        ),

        (
            "CITY",
            donor.city or "N/A",
            BLUE
        ),

        (
            "ISSUE DATE",
            certificate.donation_date.strftime("%d-%m-%Y"),
            GOLD
        ),

        (
            "DONOR ID",
            donor_id,
            PURPLE
        ),

    ]

    for index, (
        label,
        value,
        accent
    ) in enumerate(details):

        x = start_x + index * (
            card_width + gap
        )

        pdf.setFillColor(LIGHT)

        pdf.setStrokeColor(BORDER)

        pdf.setLineWidth(0.8)

        pdf.roundRect(
            x,
            cards_y,
            card_width,
            card_height,
            9,
            fill=1,
            stroke=1
        )

        pdf.setFillColor(accent)

        pdf.roundRect(
            x,
            cards_y + card_height - 5,
            card_width,
            5,
            3,
            fill=1,
            stroke=0
        )

        pdf.setFillColor(MUTED)

        pdf.setFont(
            "Helvetica-Bold",
            6.5
        )

        pdf.drawCentredString(
            x + card_width / 2,
            cards_y + 33,
            label
        )

        display_value = str(value)

        font_size = (
            7.5
            if len(display_value) > 18
            else 10
        )

        pdf.setFillColor(NAVY)

        pdf.setFont(
            "Helvetica-Bold",
            font_size
        )

        pdf.drawCentredString(
            x + card_width / 2,
            cards_y + 16,
            display_value
        )

    # -----------------------------------------------------
    # QR CODE
    # -----------------------------------------------------

    qr_x = page_width - 148
    qr_y = page_height - 292
    qr_size = 72

    pdf.setFillColor(WHITE)

    pdf.setStrokeColor(BLUE)
    pdf.setLineWidth(1.5)

    pdf.roundRect(
        qr_x - 9,
        qr_y - 9,
        qr_size + 18,
        qr_size + 34,
        9,
        fill=1,
        stroke=1
    )

    pdf.drawImage(
        ImageReader(qr_buffer),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto"
    )

    pdf.setFillColor(GREEN)

    pdf.setFont(
        "Helvetica-Bold",
        7
    )

    pdf.drawCentredString(
        qr_x + qr_size / 2,
        qr_y - 20,
        "VERIFIED"
    )

    # -----------------------------------------------------
    # QUOTE
    # -----------------------------------------------------

    pdf.setFillColor(MUTED)

    pdf.setFont(
        "Helvetica-Oblique",
        8
    )

    pdf.drawCentredString(
        page_width / 2,
        68,
        '"Every drop donated can become someone\'s hope in a critical moment."'
    )

    # -----------------------------------------------------
    # CERTIFICATE NUMBER
    # -----------------------------------------------------

    pdf.setFillColor(NAVY)

    pdf.setFont(
        "Helvetica-Bold",
        6.8
    )

    pdf.drawCentredString(
        page_width / 2,
        27,
        f"Certificate No. {certificate_number}"
    )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    pdf.setFillColor(CORAL)

    pdf.setFont(
        "Helvetica-Bold",
        7
    )

    pdf.drawCentredString(
        page_width / 2,
        15,
        "SAVE BLOOD • SAVE LIVES • SUPPORT IN EMERGENCIES"
    )

    # -----------------------------------------------------
    # FINISH PDF
    # -----------------------------------------------------

    pdf.showPage()

    pdf.save()

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="BloodLink_Certificate_'
        f'{certificate_number}.pdf"'
    )

    return response


# =========================================================
# MARK DONATION
# =========================================================

@require_POST
@login_required
def mark_donation(request, id):

    donor = get_object_or_404(
        UserProfile,
        id=id
    )

    with transaction.atomic():

        donor.donation_count += 1

        donor.save(
            update_fields=["donation_count"]
        )

        certificate = DonationCertificate.objects.create(

            donor=donor,

            donation_date=timezone.localdate(),

            certificate_number=(
                f"BL-{donor.id}-"
                f"{uuid4().hex[:8].upper()}"
            )
        )

    messages.success(
        request,
        "Donation marked successfully!"
    )

    # तुमच्या urls.py मध्ये certificate view असल्यास
    # हा redirect चालेल.
    return redirect(
        "certificate",
        id=certificate.id
    )


# =========================================================
# VERIFY CERTIFICATE
# =========================================================

def verify_certificate(
    request,
    certificate_number
):

    certificate = get_object_or_404(

        DonationCertificate.objects.select_related(
            "donor",
            "donor__user"
        ),

        certificate_number=certificate_number

    )

    return render(
        request,
        "accounts/verify_certificate.html",
        {
            "certificate": certificate,
            "donor": certificate.donor,
        }
    )


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

@login_required
def notifications(request):

    user_notifications = (

        Notification.objects
        .filter(user=request.user)
        .select_related("emergency")
        .order_by("-created_at")

    )

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

    unread_count = user_notifications.filter(
        is_read=False
    ).count()

    return render(
        request,
        "accounts/notifications.html",
        {
            "notifications": user_notifications,
            "unread_count": unread_count,
        }
    )


# =========================================================
# ACCEPT EMERGENCY
# =========================================================

@require_POST
@login_required
def accept_emergency(
    request,
    emergency_id
):

    emergency = get_object_or_404(
        EmergencyRequest,
        id=emergency_id
    )

    if emergency.status not in [
        "ACTIVE",
        "MATCHED"
    ]:

        messages.warning(
            request,
            "This emergency request is no longer active."
        )

        return redirect("notifications")

    donor, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    with transaction.atomic():

        response, created = (
            EmergencyResponse.objects.get_or_create(

                emergency=emergency,

                donor=donor,

                defaults={
                    "response": "ACCEPTED"
                }

            )
        )

        if not created:

            response.response = "ACCEPTED"

            response.save(
                update_fields=["response"]
            )

        if emergency.status == "ACTIVE":

            emergency.status = "MATCHED"

            emergency.save(
                update_fields=["status"]
            )

    messages.success(
        request,
        "You have accepted the emergency request."
    )

    return redirect("notifications")


# =========================================================
# REJECT EMERGENCY
# =========================================================

@require_POST
@login_required
def reject_emergency(
    request,
    emergency_id
):

    emergency = get_object_or_404(
        EmergencyRequest,
        id=emergency_id
    )

    donor, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    with transaction.atomic():

        response, created = (
            EmergencyResponse.objects.get_or_create(

                emergency=emergency,

                donor=donor,

                defaults={
                    "response": "REJECTED"
                }

            )
        )

        if not created:

            response.response = "REJECTED"

            response.save(
                update_fields=["response"]
            )

    messages.info(
        request,
        "You have rejected the emergency request."
    )

    return redirect("notifications")


# =========================================================
# ADMIN ACTIVE EMERGENCY API
# =========================================================

@login_required
def admin_active_emergency_api(request):

    if not request.user.is_superuser:

        return JsonResponse(
            {
                "success": False,
                "message": "Unauthorized"
            },
            status=403
        )

    emergencies = (

        EmergencyRequest.objects
        .filter(status="ACTIVE")
        .order_by("-created_at")[:20]

    )

    data = []

    for emergency in emergencies:

        data.append(

            {

                "id": emergency.id,

                "patient_name":
                    emergency.patient_name,

                "blood_group":
                    emergency.blood_group,

                "units_required":
                    emergency.units_required,

                "hospital_name":
                    emergency.hospital_name,

                "city":
                    emergency.city,

                "contact_number":
                    emergency.contact_number,

                "emergency_type":
                    emergency.emergency_type,

                "urgency":
                    emergency.urgency,

                "created_at":
                    emergency.created_at.isoformat(),

            }

        )

    return JsonResponse(
        {

            "success": True,

            "count": len(data),

            "emergencies": data,

        }
    )