from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        DONOR = "donor", "Donor"
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
        AMBULANCE_OPERATOR = "ambulance_operator", "Ambulance Operator"
        SYSTEM_ADMIN = "system_admin", "System Admin"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.DONOR)


class Donor(models.Model):
    BLOOD_TYPES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="donor")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, default="O+")
    last_donation_date = models.DateField(blank=True, null=True)

    @property
    def is_eligible(self):
        if not self.last_donation_date:
            return True
        return timezone.localdate() >= self.next_eligible_date

    @property
    def next_eligible_date(self):
        if not self.last_donation_date:
            return timezone.localdate()
        return self.last_donation_date + timedelta(days=56)

    def __str__(self):
        return f"{self.user.username} ({self.blood_type})"
