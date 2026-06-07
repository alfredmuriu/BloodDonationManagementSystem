# Blood Donation Management System

Minimal Django demo for:

- Authentication for donor, hospital admin, ambulance operator, and system admin users
- Donor management with blood type and 56-day eligibility rule
- MySQL-backed persistence

## Setup

```powershell
cd "C:\Users\sebag\OneDrive\Documents\3.1  ICS\Blood bank"
python -m pip install -r requirements.txt
```

Create a MySQL database:

```sql
CREATE DATABASE bloodbank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

If your MySQL user is not `root` with a blank password, set these before migrating:

```powershell
$env:MYSQL_DATABASE="bloodbank"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_mysql_password"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
```

Run migrations and start the server:

```powershell
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Demo Flow

Register users with these roles:

- `ethan` as `Donor`
- `hospital1` as `Hospital Admin`
- `ambulance1` as `Ambulance Operator`
- `admin1` as `System Admin`

Then log in with each account and confirm each role lands on its own dashboard.

Useful MySQL demo queries:

```sql
SELECT * FROM core_user;
SELECT * FROM core_donor;
```
