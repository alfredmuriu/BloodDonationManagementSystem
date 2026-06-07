from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Donor, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Blood Bank", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Blood Bank", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("user", "blood_type", "last_donation_date", "is_eligible")
