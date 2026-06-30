from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

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

COUNTY_NAMES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet", "Embu", "Garissa",
    "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho", "Kiambu", "Kilifi",
    "Kirinyaga", "Kisii", "Kisumu", "Kitui", "Kwale", "Laikipia", "Lamu",
    "Machakos", "Makueni", "Mandera", "Marsabit", "Meru", "Migori", "Mombasa",
    "Murang'a", "Nairobi", "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua",
    "Nyeri", "Samburu", "Siaya", "Taita-Taveta", "Tana River", "Tharaka-Nithi",
    "Trans Nzoia", "Turkana", "Uasin Gishu", "Vihiga", "Wajir", "West Pokot",
]

COUNTIES = [(name, name) for name in COUNTY_NAMES]


class User(AbstractUser):
    class Role(models.TextChoices):
        DONOR = "donor", "Donor"
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
        AMBULANCE_OPERATOR = "ambulance_operator", "Ambulance Operator"
        SYSTEM_ADMIN = "system_admin", "System Admin"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.DONOR)


class Hospital(models.Model):
    name = models.CharField(max_length=100)
    county = models.CharField(max_length=50, choices=COUNTIES, default="Nairobi")
    manager = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="hospital"
    )

    def __str__(self):
        return self.name


class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="donor")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, default="O+")
    date_of_birth = models.DateField(blank=True, null=True)
    county = models.CharField(max_length=50, choices=COUNTIES, blank=True)
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


class Appointment(models.Model):
    STATUS = [
        ("booked", "Booked"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name="appointments")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default="booked")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.user.username} @ {self.hospital.name} ({self.date})"


class BloodUnit(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="units")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    collection_date = models.DateField(default=timezone.localdate)
    expiry_date = models.DateField(blank=True, null=True)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expiry_date:
            self.expiry_date = self.collection_date + timedelta(days=42)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.localdate() > self.expiry_date

    @property
    def days_to_expiry(self):
        return (self.expiry_date - timezone.localdate()).days

    def __str__(self):
        return f"{self.blood_type} unit at {self.hospital.name}"


class BloodRequest(models.Model):
    PRIORITY = [
        ("critical", "Critical"),
        ("urgent", "Urgent"),
        ("normal", "Normal"),
    ]
    STATUS = [
        ("pending", "Pending"),
        ("fulfilled", "Fulfilled"),
        ("cancelled", "Cancelled"),
    ]

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="requests")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    units_needed = models.PositiveIntegerField(default=1)
    priority = models.CharField(max_length=10, choices=PRIORITY, default="normal")
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def priority_rank(self):
        order = {"critical": 1, "urgent": 2, "normal": 3}
        return order.get(self.priority, 9)

    def __str__(self):
        return f"{self.blood_type} x{self.units_needed} ({self.priority})"


class Ambulance(models.Model):
    operator = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ambulance"
    )
    plate_number = models.CharField(max_length=20)
    county = models.CharField(max_length=50, choices=COUNTIES, default="Nairobi")
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.plate_number} ({self.county})"


class Dispatch(models.Model):
    STATUS = [
        ("dispatched", "Dispatched"),
        ("delivered", "Delivered"),
    ]

    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name="dispatches")
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE, related_name="dispatches")
    status = models.CharField(max_length=10, choices=STATUS, default="dispatched")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispatch {self.ambulance.plate_number} -> {self.request.hospital.name}"
