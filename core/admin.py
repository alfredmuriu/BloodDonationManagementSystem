from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Ambulance,
    Appointment,
    BloodRequest,
    BloodUnit,
    Dispatch,
    Donor,
    Hospital,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Blood Bank", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Blood Bank", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("user", "blood_type", "county", "last_donation_date", "is_eligible")


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "county", "manager")


@admin.register(BloodUnit)
class BloodUnitAdmin(admin.ModelAdmin):
    list_display = ("blood_type", "hospital", "collection_date", "expiry_date", "is_used")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("donor", "hospital", "date", "status")


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ("blood_type", "units_needed", "priority", "status", "hospital")


@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "county", "operator", "is_available")


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = ("ambulance", "request", "status", "created_at")
