from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import (
    Ambulance,
    BloodUnit,
    BloodRequest,
    Donor,
    Hospital,
    User,
)

DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    ("ethan", User.Role.DONOR),
    ("hospital1", User.Role.HOSPITAL_ADMIN),
    ("ambulance1", User.Role.AMBULANCE_OPERATOR),
    ("admin1", User.Role.SYSTEM_ADMIN),
]


class Command(BaseCommand):
    help = "Seed demo accounts and sample data for all four modules."

    def handle(self, *args, **options):
        users = {}
        for username, role in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={"role": role}
            )
            # Always (re)set password, role and email so every demo login is
            # guaranteed to work, even for pre-existing accounts.
            user.set_password(DEMO_PASSWORD)
            user.role = role
            user.email = f"{username}@example.com"
            # System admin doubles as a Django superuser so it can use the
            # built-in /admin/ site for full CRUD on every model.
            if role == User.Role.SYSTEM_ADMIN:
                user.is_staff = True
                user.is_superuser = True
            user.save()
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} {username} ({role})"))
            users[username] = user

        # Donor profile for ethan: donated 10 days ago -> currently INELIGIBLE.
        ethan = users["ethan"]
        donor, _ = Donor.objects.get_or_create(user=ethan)
        donor.blood_type = "O+"
        donor.county = "Nairobi"
        donor.date_of_birth = date(1998, 5, 20)
        donor.weight_kg = 72
        donor.last_donation_date = date.today() - timedelta(days=10)
        donor.save()

        # Hospital linked to hospital1
        hospital, _ = Hospital.objects.get_or_create(
            name="Nairobi General Hospital",
            defaults={"county": "Nairobi", "manager": users["hospital1"]},
        )
        if hospital.manager is None:
            hospital.manager = users["hospital1"]
            hospital.save()

        # Some blood units, including one expiring soon
        if hospital.units.count() == 0:
            BloodUnit.objects.create(hospital=hospital, blood_type="O+")
            BloodUnit.objects.create(hospital=hospital, blood_type="A+")
            BloodUnit.objects.create(
                hospital=hospital,
                blood_type="O-",
                collection_date=date.today() - timedelta(days=38),
            )

        # Ambulance linked to ambulance1
        Ambulance.objects.get_or_create(
            plate_number="KDA 123A",
            defaults={"county": "Nairobi", "operator": users["ambulance1"]},
        )

        # A pending normal request to populate the queue
        if hospital.requests.count() == 0:
            BloodRequest.objects.create(
                hospital=hospital, blood_type="A+", units_needed=2, priority="urgent"
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nDone. All demo passwords: {DEMO_PASSWORD}")
        )
