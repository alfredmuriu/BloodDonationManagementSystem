"""Populate the system with realistic demo data across every entity.

Safe to run more than once: it tops up each entity toward a target count and
fills in missing donor details rather than duplicating or overwriting.
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import (
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

PASSWORD = "Password123!"

FIRST_NAMES = [
    "Amina", "Brian", "Grace", "Kevin", "Mercy", "Daniel", "Faith", "Samuel",
    "Joyce", "Peter", "Esther", "John", "Cynthia", "Dennis", "Lucy", "Victor",
    "Nancy", "James", "Caroline", "Michael", "Alice", "David", "Ann", "Collins",
    "Winnie", "Eric", "Ruth", "George", "Beatrice", "Paul", "Sharon", "Anthony",
]
LAST_NAMES = [
    "Wanjiru", "Otieno", "Achieng", "Mwangi", "Kamau", "Njoroge", "Ochieng",
    "Wafula", "Kiprop", "Chebet", "Mutua", "Barasa", "Owino", "Kariuki",
    "Cheruiyot", "Muthoni", "Odhiambo", "Kimani", "Wekesa", "Nyambura",
]

# (name, county) — real Kenyan referral hospitals
HOSPITALS = [
    ("Kenyatta National Hospital", "Nairobi"),
    ("Moi Teaching & Referral Hospital", "Uasin Gishu"),
    ("Aga Khan University Hospital", "Nairobi"),
    ("Coast General Teaching Hospital", "Mombasa"),
    ("Nakuru Level 5 Hospital", "Nakuru"),
    ("Jaramogi Oginga Odinga Referral", "Kisumu"),
]

BLOOD_CODES = [c for c, _ in BLOOD_TYPES]


class Command(BaseCommand):
    help = "Add realistic demo data (names, hospitals, units, requests, etc.)."

    def handle(self, *args, **options):
        random.seed(2026)
        self._name_users()
        self._enrich_donors()
        hospitals = self._make_hospitals()
        self._make_ambulances()
        self._make_units(hospitals)
        requests = self._make_requests(hospitals)
        self._make_appointments(hospitals)
        self._make_dispatches(requests)
        self.stdout.write(self.style.SUCCESS("\nBulk demo data ready."))
        self.stdout.write(
            f"Hospitals: {Hospital.objects.count()} | "
            f"Donors: {Donor.objects.count()} | "
            f"Units: {BloodUnit.objects.count()} | "
            f"Requests: {BloodRequest.objects.count()} | "
            f"Ambulances: {Ambulance.objects.count()} | "
            f"Appointments: {Appointment.objects.count()} | "
            f"Dispatches: {Dispatch.objects.count()}"
        )

    # -- users get real names ------------------------------------------------
    def _name_users(self):
        for user in User.objects.all():
            if not user.first_name:
                user.first_name = random.choice(FIRST_NAMES)
                user.last_name = random.choice(LAST_NAMES)
                user.save()
        self.stdout.write("Assigned real names to users.")

    # -- flesh out donor profiles -------------------------------------------
    def _enrich_donors(self):
        # Ensure every donor-role user has a profile
        for user in User.objects.filter(role=User.Role.DONOR):
            Donor.objects.get_or_create(user=user)

        counties = ["Nairobi", "Kisumu", "Mombasa", "Nakuru", "Uasin Gishu", "Kiambu"]
        for i, donor in enumerate(Donor.objects.all()):
            if not donor.county:
                donor.county = random.choice(counties)
            if not donor.date_of_birth:
                age = random.randint(19, 55)
                donor.date_of_birth = date.today() - timedelta(days=age * 365 + random.randint(0, 364))
            if not donor.weight_kg:
                donor.weight_kg = random.randint(55, 90)
            if not donor.blood_type:
                donor.blood_type = random.choice(BLOOD_CODES)
            # Vary last donation so some are eligible and some are not
            if donor.last_donation_date is None and i % 3 == 0:
                donor.last_donation_date = date.today() - timedelta(days=random.choice([20, 30, 70, 120]))
            donor.save()
        self.stdout.write("Enriched donor profiles.")

    # -- hospitals + their managers -----------------------------------------
    def _make_hospitals(self):
        hospitals = []
        for idx, (name, county) in enumerate(HOSPITALS, start=1):
            hospital, created = Hospital.objects.get_or_create(
                name=name, defaults={"county": county}
            )
            if hospital.manager is None:
                username = f"hadmin{idx}"
                manager, umade = User.objects.get_or_create(
                    username=username,
                    defaults={"role": User.Role.HOSPITAL_ADMIN},
                )
                if umade:
                    manager.set_password(PASSWORD)
                    manager.role = User.Role.HOSPITAL_ADMIN
                    manager.first_name = random.choice(FIRST_NAMES)
                    manager.last_name = random.choice(LAST_NAMES)
                    manager.email = f"{username}@example.com"
                    manager.save()
                hospital.manager = manager
                hospital.save()
            hospitals.append(hospital)
        self.stdout.write(f"Hospitals ready ({len(hospitals)}).")
        return hospitals

    # -- ambulances + operators ---------------------------------------------
    def _make_ambulances(self):
        plates = ["KDA 123A", "KCX 445T", "KDG 902M", "KBZ 771P", "KDE 318L"]
        counties = ["Nairobi", "Uasin Gishu", "Mombasa", "Nakuru", "Kisumu"]
        for idx, (plate, county) in enumerate(zip(plates, counties), start=1):
            amb, created = Ambulance.objects.get_or_create(
                plate_number=plate, defaults={"county": county}
            )
            if amb.operator is None:
                username = f"ambop{idx}"
                op, umade = User.objects.get_or_create(
                    username=username,
                    defaults={"role": User.Role.AMBULANCE_OPERATOR},
                )
                if umade:
                    op.set_password(PASSWORD)
                    op.role = User.Role.AMBULANCE_OPERATOR
                    op.first_name = random.choice(FIRST_NAMES)
                    op.last_name = random.choice(LAST_NAMES)
                    op.email = f"{username}@example.com"
                    op.save()
                amb.operator = op
                amb.save()
        self.stdout.write(f"Ambulances ready ({Ambulance.objects.count()}).")

    # -- blood inventory -----------------------------------------------------
    def _make_units(self, hospitals):
        target = 28
        existing = BloodUnit.objects.count()
        for _ in range(max(0, target - existing)):
            hospital = random.choice(hospitals)
            # spread collection dates so some units are near expiry (42-day life)
            collected = date.today() - timedelta(days=random.randint(0, 40))
            BloodUnit.objects.create(
                hospital=hospital,
                blood_type=random.choice(BLOOD_CODES),
                collection_date=collected,
                is_used=random.random() < 0.15,
            )
        self.stdout.write(f"Blood units ready ({BloodUnit.objects.count()}).")

    # -- blood requests ------------------------------------------------------
    def _make_requests(self, hospitals):
        target = 9
        priorities = ["critical", "urgent", "normal", "normal", "urgent"]
        statuses = ["pending", "pending", "pending", "fulfilled"]
        existing = list(BloodRequest.objects.all())
        for _ in range(max(0, target - len(existing))):
            BloodRequest.objects.create(
                hospital=random.choice(hospitals),
                blood_type=random.choice(BLOOD_CODES),
                units_needed=random.randint(1, 4),
                priority=random.choice(priorities),
                status=random.choice(statuses),
            )
        self.stdout.write(f"Blood requests ready ({BloodRequest.objects.count()}).")
        return list(BloodRequest.objects.all())

    # -- donation appointments ----------------------------------------------
    def _make_appointments(self, hospitals):
        donors = list(Donor.objects.all())
        if not donors:
            return
        target = 8
        statuses = ["booked", "booked", "completed", "cancelled"]
        existing = Appointment.objects.count()
        for _ in range(max(0, target - existing)):
            Appointment.objects.create(
                donor=random.choice(donors),
                hospital=random.choice(hospitals),
                date=date.today() + timedelta(days=random.randint(-20, 20)),
                status=random.choice(statuses),
            )
        self.stdout.write(f"Appointments ready ({Appointment.objects.count()}).")

    # -- dispatches for the most urgent requests ----------------------------
    def _make_dispatches(self, requests):
        ambulances = list(Ambulance.objects.all())
        if not ambulances:
            return
        urgent = [r for r in requests if r.priority in ("critical", "urgent")]
        random.shuffle(urgent)
        target = 3
        made = Dispatch.objects.count()
        for req in urgent:
            if Dispatch.objects.count() - made >= target:
                break
            if req.dispatches.exists():
                continue
            Dispatch.objects.create(
                request=req,
                ambulance=random.choice(ambulances),
                status=random.choice(["dispatched", "delivered"]),
            )
        self.stdout.write(f"Dispatches ready ({Dispatch.objects.count()}).")
