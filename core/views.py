from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserRegistrationForm
from .models import Donor, User


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
        donor, _ = Donor.objects.get_or_create(user=user, defaults={"blood_type": "O+"})
        return render(
            request,
            "donor_dashboard.html",
            {"donor": donor, "next_date": donor.next_eligible_date},
        )
    if user.role == User.Role.HOSPITAL_ADMIN:
        return render(request, "hospital_dashboard.html")
    if user.role == User.Role.AMBULANCE_OPERATOR:
        return render(request, "ambulance_dashboard.html")
    return render(request, "admin_dashboard.html")
