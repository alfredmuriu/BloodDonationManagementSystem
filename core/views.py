from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AppointmentForm,
    BloodRequestForm,
    BloodUnitForm,
    DonorProfileForm,
    UserRegistrationForm,
)
from .models import (
    Ambulance,
    Appointment,
    BloodRequest,
    BloodUnit,
    Dispatch,
    Donor,
    Hospital,
    User,
    BLOOD_TYPES,
)


def index(request):
    return render(request, "index.html")


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
    else:
        form = UserRegistrationForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    user = request.user
    if user.role == User.Role.DONOR:
        return donor_dashboard(request)
    if user.role == User.Role.HOSPITAL_ADMIN:
        return hospital_dashboard(request)
    if user.role == User.Role.AMBULANCE_OPERATOR:
        return ambulance_dashboard(request)
    return admin_dashboard(request)


# ---------- Donor module ----------

def donor_dashboard(request):
    donor, _ = Donor.objects.get_or_create(
        user=request.user, defaults={"blood_type": "O+"}
    )
    appointments = donor.appointments.order_by("-date")
    return render(
        request,
        "donor_dashboard.html",
        {
            "donor": donor,
            "next_date": donor.next_eligible_date,
            "appointments": appointments,
        },
    )


@login_required
def donor_profile(request):
    donor, _ = Donor.objects.get_or_create(
        user=request.user, defaults={"blood_type": "O+"}
    )
    if request.method == "POST":
        form = DonorProfileForm(request.POST, instance=donor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved.")
            return redirect("dashboard")
    else:
        form = DonorProfileForm(instance=donor)
    return render(request, "donor_profile.html", {"form": form, "donor": donor})


@login_required
def book_appointment(request):
    donor, _ = Donor.objects.get_or_create(
        user=request.user, defaults={"blood_type": "O+"}
    )
    if not donor.is_eligible:
        messages.error(request, "You are not eligible to donate yet.")
        return redirect("dashboard")

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.donor = donor
            appointment.save()
            if request.user.email:
                send_mail(
                    "Appointment Confirmed",
                    f"Your donation appointment at {appointment.hospital.name} "
                    f"is booked for {appointment.date}.",
                    None,
                    [request.user.email],
                    fail_silently=True,
                )
            messages.success(request, "Appointment booked.")
            return redirect("dashboard")
    else:
        form = AppointmentForm()
    return render(request, "book_appointment.html", {"form": form})


# ---------- Hospital inventory module ----------

def get_hospital(user):
    return Hospital.objects.filter(manager=user).first()


def hospital_dashboard(request):
    hospital = get_hospital(request.user)
    if hospital is None:
        return render(request, "hospital_dashboard.html", {"hospital": None})

    units = hospital.units.filter(is_used=False).order_by("expiry_date")
    stock = {}
    for code, _ in BLOOD_TYPES:
        stock[code] = units.filter(blood_type=code).count()

    expiring = [u for u in units if not u.is_expired and u.days_to_expiry <= 7]
    requests = hospital.requests.order_by("-created_at")

    return render(
        request,
        "hospital_dashboard.html",
        {
            "hospital": hospital,
            "units": units,
            "stock": stock,
            "expiring": expiring,
            "requests": requests,
        },
    )


@login_required
def add_unit(request):
    hospital = get_hospital(request.user)
    if hospital is None:
        messages.error(request, "No hospital linked to your account.")
        return redirect("dashboard")

    if request.method == "POST":
        form = BloodUnitForm(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.hospital = hospital
            unit.save()
            messages.success(request, "Blood unit added.")
            return redirect("dashboard")
    else:
        form = BloodUnitForm()
    return render(request, "add_unit.html", {"form": form})


@login_required
def create_request(request):
    hospital = get_hospital(request.user)
    if hospital is None:
        messages.error(request, "No hospital linked to your account.")
        return redirect("dashboard")

    if request.method == "POST":
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.hospital = hospital
            blood_request.save()
            if blood_request.priority == "critical":
                dispatch_ambulance(blood_request)
            messages.success(request, "Blood request submitted.")
            return redirect("dashboard")
    else:
        form = BloodRequestForm()
    return render(request, "create_request.html", {"form": form})


# ---------- Priority request queue ----------

def admin_dashboard(request):
    requests = list(BloodRequest.objects.filter(status="pending"))
    requests.sort(key=lambda r: (r.priority_rank, r.created_at))
    return render(
        request,
        "admin_dashboard.html",
        {
            "requests": requests,
            "donor_count": Donor.objects.count(),
            "hospital_count": Hospital.objects.count(),
            "unit_count": BloodUnit.objects.filter(is_used=False).count(),
            "ambulance_count": Ambulance.objects.count(),
        },
    )


@login_required
def fulfill_request(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    blood_request.status = "fulfilled"
    blood_request.save()
    messages.success(request, "Request marked as fulfilled.")
    return redirect("dashboard")


# ---------- Ambulance dispatch ----------

def dispatch_ambulance(blood_request):
    ambulance = Ambulance.objects.filter(
        county=blood_request.hospital.county, is_available=True
    ).first()
    if ambulance is None:
        ambulance = Ambulance.objects.filter(is_available=True).first()
    if ambulance:
        ambulance.is_available = False
        ambulance.save()
        Dispatch.objects.create(request=blood_request, ambulance=ambulance)


def ambulance_dashboard(request):
    ambulance = Ambulance.objects.filter(operator=request.user).first()
    dispatches = []
    if ambulance:
        dispatches = ambulance.dispatches.order_by("-created_at")
    return render(
        request,
        "ambulance_dashboard.html",
        {"ambulance": ambulance, "dispatches": dispatches},
    )


@login_required
def complete_dispatch(request, dispatch_id):
    dispatch = get_object_or_404(Dispatch, id=dispatch_id)
    dispatch.status = "delivered"
    dispatch.save()
    dispatch.ambulance.is_available = True
    dispatch.ambulance.save()
    messages.success(request, "Dispatch marked as delivered.")
    return redirect("dashboard")
