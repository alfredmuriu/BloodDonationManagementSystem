from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from django.http import Http404

from .forms import (
    AdminAmbulanceForm,
    AdminAppointmentForm,
    AdminBloodRequestForm,
    AdminBloodUnitForm,
    AdminDispatchForm,
    AdminDonorForm,
    AdminHospitalForm,
    AdminUserForm,
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
        messages.error(
            request,
            "You are not eligible to donate yet: " + " ".join(donor.eligibility_issues),
        )
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
            "nav": _nav_items(None),
            "requests": requests,
            "donor_count": Donor.objects.count(),
            "hospital_count": Hospital.objects.count(),
            "unit_count": BloodUnit.objects.filter(is_used=False).count(),
            "ambulance_count": Ambulance.objects.count(),
            "user_count": User.objects.count(),
            "request_count": BloodRequest.objects.count(),
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


# ===========================================================================
# Admin control panel: full CRUD on every category (system admin only)
# ===========================================================================

def _dash(o):
    """Render a value for a table cell, using an em dash for blanks."""
    return o if (o not in (None, "")) else "—"


# Each entry: model, form, singular/plural labels, and the columns to list.
# Columns are (header, callable(obj) -> displayed value).
ADMIN_REGISTRY = {
    "users": {
        "model": User,
        "form": AdminUserForm,
        "singular": "User",
        "label": "Users",
        "queryset": lambda: User.objects.order_by("username"),
        "columns": [
            ("Name", lambda o: o.get_full_name() or "—"),
            ("Username", lambda o: o.username),
            ("Email", lambda o: _dash(o.email)),
            ("Role", lambda o: o.get_role_display()),
            ("Active", lambda o: "Yes" if o.is_active else "No"),
        ],
    },
    "donors": {
        "model": Donor,
        "form": AdminDonorForm,
        "singular": "Donor",
        "label": "Donors",
        "queryset": lambda: Donor.objects.select_related("user").order_by("user__username"),
        "columns": [
            ("Name", lambda o: o.user.get_full_name() or o.user.username),
            ("Blood Type", lambda o: o.blood_type),
            ("County", lambda o: _dash(o.county)),
            ("Age", lambda o: o.age if o.age is not None else "—"),
            ("Weight", lambda o: f"{o.weight_kg} kg" if o.weight_kg else "—"),
            ("Eligible", lambda o: "Yes" if o.is_eligible else "No"),
        ],
    },
    "hospitals": {
        "model": Hospital,
        "form": AdminHospitalForm,
        "singular": "Hospital",
        "label": "Hospitals",
        "queryset": lambda: Hospital.objects.select_related("manager").order_by("name"),
        "columns": [
            ("Name", lambda o: o.name),
            ("County", lambda o: o.county),
            ("Manager", lambda o: o.manager.username if o.manager else "—"),
        ],
    },
    "units": {
        "model": BloodUnit,
        "form": AdminBloodUnitForm,
        "singular": "Blood Unit",
        "label": "Blood Units",
        "queryset": lambda: BloodUnit.objects.select_related("hospital").order_by("expiry_date"),
        "columns": [
            ("Blood Type", lambda o: o.blood_type),
            ("Hospital", lambda o: o.hospital.name),
            ("Collected", lambda o: o.collection_date),
            ("Expires", lambda o: o.expiry_date),
            ("Used", lambda o: "Yes" if o.is_used else "No"),
        ],
    },
    "requests": {
        "model": BloodRequest,
        "form": AdminBloodRequestForm,
        "singular": "Blood Request",
        "label": "Blood Requests",
        "queryset": lambda: BloodRequest.objects.select_related("hospital").order_by("-created_at"),
        "columns": [
            ("Hospital", lambda o: o.hospital.name),
            ("Blood Type", lambda o: o.blood_type),
            ("Units", lambda o: o.units_needed),
            ("Priority", lambda o: o.get_priority_display()),
            ("Status", lambda o: o.get_status_display()),
        ],
    },
    "ambulances": {
        "model": Ambulance,
        "form": AdminAmbulanceForm,
        "singular": "Ambulance",
        "label": "Ambulances",
        "queryset": lambda: Ambulance.objects.select_related("operator").order_by("plate_number"),
        "columns": [
            ("Plate", lambda o: o.plate_number),
            ("County", lambda o: o.county),
            ("Operator", lambda o: o.operator.username if o.operator else "—"),
            ("Available", lambda o: "Yes" if o.is_available else "No"),
        ],
    },
    "appointments": {
        "model": Appointment,
        "form": AdminAppointmentForm,
        "singular": "Appointment",
        "label": "Appointments",
        "queryset": lambda: Appointment.objects.select_related("donor__user", "hospital").order_by("-date"),
        "columns": [
            ("Donor", lambda o: o.donor.user.username),
            ("Hospital", lambda o: o.hospital.name),
            ("Date", lambda o: o.date),
            ("Status", lambda o: o.get_status_display()),
        ],
    },
    "dispatches": {
        "model": Dispatch,
        "form": AdminDispatchForm,
        "singular": "Dispatch",
        "label": "Dispatches",
        "queryset": lambda: Dispatch.objects.select_related("ambulance", "request__hospital").order_by("-created_at"),
        "columns": [
            ("Ambulance", lambda o: o.ambulance.plate_number),
            ("Destination", lambda o: o.request.hospital.name),
            ("Status", lambda o: o.get_status_display()),
            ("Created", lambda o: o.created_at.strftime("%Y-%m-%d %H:%M")),
        ],
    },
}

# Order shown in the sidebar.
ADMIN_NAV = ["users", "donors", "hospitals", "units", "requests", "ambulances", "appointments", "dispatches"]


def _is_system_admin(user):
    return user.is_authenticated and user.role == User.Role.SYSTEM_ADMIN


def _get_entry(slug):
    entry = ADMIN_REGISTRY.get(slug)
    if entry is None:
        raise Http404("Unknown admin section")
    return entry


def _nav_items(active):
    return [
        {"slug": s, "label": ADMIN_REGISTRY[s]["label"], "active": s == active}
        for s in ADMIN_NAV
    ]


@login_required
def manage_list(request, model):
    if not _is_system_admin(request.user):
        messages.error(request, "Admin access only.")
        return redirect("dashboard")
    entry = _get_entry(model)
    columns = entry["columns"]
    rows = [
        {"pk": obj.pk, "cells": [fn(obj) for _, fn in columns]}
        for obj in entry["queryset"]()
    ]
    return render(request, "manage_list.html", {
        "nav": _nav_items(model),
        "slug": model,
        "label": entry["label"],
        "singular": entry["singular"],
        "headers": [h for h, _ in columns],
        "rows": rows,
        "count": len(rows),
    })


@login_required
def manage_form(request, model, pk=None):
    if not _is_system_admin(request.user):
        messages.error(request, "Admin access only.")
        return redirect("dashboard")
    entry = _get_entry(model)
    instance = get_object_or_404(entry["model"], pk=pk) if pk is not None else None
    FormClass = entry["form"]
    if request.method == "POST":
        form = FormClass(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            verb = "updated" if instance else "created"
            messages.success(request, f"{entry['singular']} {verb} successfully.")
            return redirect("manage_list", model=model)
    else:
        form = FormClass(instance=instance)
    return render(request, "manage_form.html", {
        "nav": _nav_items(model),
        "slug": model,
        "label": entry["label"],
        "singular": entry["singular"],
        "form": form,
        "is_add": instance is None,
    })


@login_required
def manage_delete(request, model, pk):
    if not _is_system_admin(request.user):
        messages.error(request, "Admin access only.")
        return redirect("dashboard")
    entry = _get_entry(model)
    obj = get_object_or_404(entry["model"], pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"{entry['singular']} deleted.")
        return redirect("manage_list", model=model)
    return render(request, "manage_delete.html", {
        "nav": _nav_items(model),
        "slug": model,
        "label": entry["label"],
        "singular": entry["singular"],
        "object_label": str(obj),
        "pk": pk,
    })
