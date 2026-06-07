# Blood Bank Project Work Completed

This document summarizes the work completed for the Blood Donation Management System demo.

## Project Setup

- Cloned the repository into:

```text
C:\Users\sebag\OneDrive\Documents\3.1  ICS\Blood bank
```

- The GitHub repository was empty, so a working Django project was scaffolded from the supervisor/demo requirements.
- Created the main Django project folder:

```text
bloodbank/
```

- Created the main Django app:

```text
core/
```

- Added dependency list in:

```text
requirements.txt
```

## Django Structure Created

The project now contains:

- `manage.py`
- `bloodbank/settings.py`
- `bloodbank/urls.py`
- `bloodbank/asgi.py`
- `bloodbank/wsgi.py`
- `core/models.py`
- `core/forms.py`
- `core/views.py`
- `core/urls.py`
- `core/admin.py`
- `templates/`

## Authentication Implemented

Authentication was implemented for all required user types:

- Donor
- Hospital Administrator
- Ambulance Operator
- System Administrator

The custom user model includes a `role` field so each user can be routed to the correct dashboard after login.

## Donor Management Module

The donor module was implemented with:

- Donor profile model
- Blood type field
- Last donation date field
- Eligibility calculation
- 56-day donation rule

If a donor has not donated before, the system marks them as eligible.

If a donor has donated before, the system calculates the next eligible date by adding 56 days to the last donation date.

## MySQL Database Work

The project was configured to use MySQL instead of SQLite.

The database settings use environment variables:

- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`

Created the MySQL database:

```sql
CREATE DATABASE bloodbank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Ran Django migrations successfully, creating tables such as:

- `core_user`
- `core_donor`
- `auth_group`
- `auth_permission`
- `django_admin_log`
- `django_session`

Useful demo queries:

```sql
SELECT * FROM core_user;
SELECT * FROM core_donor;
```

## Demo Users Created

The following demo users were created:

| Username | Role | Password |
| --- | --- | --- |
| `ethan` | Donor | `Password123!` |
| `hospital1` | Hospital Administrator | `Password123!` |
| `ambulance1` | Ambulance Operator | `Password123!` |
| `admin1` | System Administrator | `Password123!` |

The donor user `ethan` also has a donor profile with blood type `O+`.

## Templates Created

The following templates were created:

- `base.html`
- `index.html`
- `register.html`
- `login.html`
- `donor_dashboard.html`
- `hospital_dashboard.html`
- `ambulance_dashboard.html`
- `admin_dashboard.html`

## Styling Improvements Completed

All pages were redesigned to look more polished and appealing.

Styling improvements include:

- Custom typography using Google Fonts
- Warm blood-bank color palette
- Gradient background
- Subtle patterned overlay
- Glass-style cards
- Rounded buttons
- Better form inputs
- Role-specific dashboards
- Dashboard metric cards
- Animated page entrance effect
- More polished homepage hero section
- Clear demo-ready text for each user role

## Pages Available

Homepage:

```text
http://127.0.0.1:8000/
```

Registration page:

```text
http://127.0.0.1:8000/register/
```

Login page:

```text
http://127.0.0.1:8000/login/
```

Dashboard:

```text
http://127.0.0.1:8000/dashboard/
```

## Demo Flow

1. Open the homepage.
2. Click Register.
3. Register a donor account.
4. Log in as the donor.
5. Show the donor dashboard with blood type and eligibility status.
6. Log out.
7. Log in as `hospital1`.
8. Show the Hospital Administrator Dashboard.
9. Log out.
10. Log in as `ambulance1`.
11. Show the Ambulance Operator Dashboard.
12. Log out.
13. Log in as `admin1`.
14. Show the System Administrator Dashboard.
15. Open MySQL Workbench and run:

```sql
SELECT * FROM core_user;
SELECT * FROM core_donor;
```

## Commands Used

Set MySQL password:

```powershell
$env:MYSQL_PASSWORD="your_mysql_password"
```

Run migrations:

```powershell
python manage.py migrate
```

Start development server:

```powershell
python manage.py runserver
```

Run Django system check:

```powershell
python manage.py check
```

## Current Status

The project currently satisfies the supervisor's three required demo items:

- Authentication for all user types
- Donor Management module
- MySQL database working

The user interface has also been polished to make the demo clearer and more professional.
