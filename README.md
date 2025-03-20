# QR Classroom Attendance Checker

A web application that streamlines attendance tracking using QR codes, allowing teachers to manage courses and attendance records while students can mark their presence by scanning a code.

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

## Features

- User authentication with teacher and student roles
- Course management for teachers
- QR code generation for attendance tracking
- Attendance recording via QR code scanning
- Comprehensive reporting and data export
