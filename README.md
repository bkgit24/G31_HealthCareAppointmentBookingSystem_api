
# HealthCare Appointment Booking System

A full-stack web application designed to facilitate the appointment booking. Users can book appointment, explore different services

## 🛠️ Tech Stack

- **Backend**: Flask (API development)
- **Frontend**: Django (API consumption and UI rendering)
- **Database**: SQLite
- **Styling**: Bootstrap

## 🚀 Features

- User registration and authentication
- Doctor servicing with admin approval
- Booking Appointments
- Doctor Listing

## 📦 Installation & Setup

1. **Clone the repository**:

   ```bash
   https://github.com/bkgit24/G31_HealthCareAppointmentBookingSystem_api.git
   cd G31_HealthcareAppointmentBookingSystem_api
   ```

2. **Set up a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

6. **Access the application**:

   Open your browser and navigate to `http://localhost:8000/`

## 📁 Project Structure

```
G31_HealthCareAppointmentBookingSystem_Django/
├── G31_HealthCareAppointmentBookingSystem_Django/
│   ├── manage.py
│   ├── ...
├── G31_HealthCareAppointmentBookingSystem_Flaskl/
│   ├── app.py
│   ├── ...
├── requirements.txt
└── README.md
```

## 👥 User Roles

- **Admin**: Approves doctor servicing
- **User**: Browses doctors,book appointments

## 🎓 Academic Project

This project was developed as part of an academic web development course to demonstrate proficiency in full-stack development using Flask and Django.
