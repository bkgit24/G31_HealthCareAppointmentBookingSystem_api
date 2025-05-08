from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from base.api_service import APIService
from base.models import MedicalRecord, LabTest, Prescription, Notification

from doctor import models as doctor_models
from base import models as base_models

def get_notifications(request):
    if request.user.is_authenticated and hasattr(request.user, 'doctor'):
        try:
            doctor = doctor_models.Doctor.objects.get(user=request.user)
            notifications = doctor_models.Notification.objects.filter(doctor=doctor)
            return {'notifications': notifications}
        except doctor_models.Doctor.DoesNotExist:
            return {'notifications': []}
    return {'notifications': []}

@login_required
def dashboard(request):
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    # Get appointments from API
    response = APIService.get_appointments(token)
    if response.get('success'):
        appointments = response['appointments']
    else:
        appointments = []
        messages.error(request, response.get('message', 'Failed to load appointments.'))
    
    # Get local notifications
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    
    return render(request, 'doctor/dashboard.html', {
        'appointments': appointments,
        'notifications': notifications
    })

@login_required
def appointments(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointments = base_models.Appointment.objects.filter(doctor=doctor)

        time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(9, 18)]

        context = {
            "appointments": appointments,
            "time_slots": time_slots,
            "today": datetime.now().date(),
        }

        return render(request, "doctor/appointments.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def appointment_detail(request, appointment_id):
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, 'Please login to view appointment details.')
        return redirect('login')
    
    # Get appointment details from API
    response = APIService.get_appointment(appointment_id, token)
    if response.get('success'):
        appointment = response['appointment']
    else:
        messages.error(request, response.get('message', 'Failed to load appointment details.'))
        return redirect('dashboard')
    
    # Get local medical records
    medical_records = MedicalRecord.objects.filter(appointment_id=appointment_id)
    lab_tests = LabTest.objects.filter(appointment_id=appointment_id)
    prescriptions = Prescription.objects.filter(appointment_id=appointment_id)
    
    return render(request, 'doctor/appointment_detail.html', {
        'appointment': appointment,
        'medical_records': medical_records,
        'lab_tests': lab_tests,
        'prescriptions': prescriptions
    })

@login_required
def cancel_appointment(request, appointment_id):
    token = request.session.get('token')
    if not token:
        messages.error(request, "Authentication required")
        return redirect('userauths:sign-in')
    
    response = APIService.delete_appointment(token, appointment_id)
    if response.get('status') == 'success':
        messages.success(request, "Appointment cancelled successfully!")
    else:
        messages.error(request, response.get('message', 'Failed to cancel appointment'))
    return redirect('doctor:appointment-list')

@login_required
def activate_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        appointment.status = "Scheduled"
        appointment.save()

        messages.success(request, "Appointment Re-Scheduled Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def complete_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        appointment.status = "Completed"
        appointment.save()

        doctor_models.Notification.objects.create(
            doctor=doctor,
            appointment=appointment,
            type="Appointment Completed"
        )

        from patient import models as patient_models
        patient_models.Notification.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            type="Appointment Completed"
        )

        messages.success(request, "Appointment Completed Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def add_medical_report(request, appointment_id):
    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        
        MedicalRecord.objects.create(
            appointment_id=appointment_id,
            diagnosis=diagnosis,
            treatment=treatment
        )
        messages.success(request, 'Medical report added successfully.')
        return redirect('appointment_detail', appointment_id=appointment_id)
    
    return render(request, 'doctor/add_medical_report.html', {'appointment_id': appointment_id})

@login_required
def edit_medical_report(request, appointment_id, medical_report_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        medical_report = base_models.MedicalRecord.objects.get(id=medical_report_id, appointment=appointment)

        if request.method == "POST":
            diagnosis = request.POST.get("diagnosis")
            treatment = request.POST.get("treatment")

            medical_report.diagnosis = diagnosis
            medical_report.treatment = treatment
            medical_report.save()

        messages.success(request, "Medical Report Updated Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist, base_models.MedicalRecord.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def add_lab_test(request, appointment_id):
    if request.method == 'POST':
        test_name = request.POST.get('test_name')
        description = request.POST.get('description')
        result = request.POST.get('result')
        
        LabTest.objects.create(
            appointment_id=appointment_id,
            test_name=test_name,
            description=description,
            result=result
        )
        messages.success(request, 'Lab test added successfully.')
        return redirect('appointment_detail', appointment_id=appointment_id)
    
    return render(request, 'doctor/add_lab_test.html', {'appointment_id': appointment_id})

@login_required
def edit_lab_test(request, appointment_id, lab_test_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        lab_test = base_models.LabTest.objects.get(id=lab_test_id, appointment=appointment)

        if request.method == "POST":
            test_name = request.POST.get("test_name")
            description = request.POST.get("description")
            result = request.POST.get("result")

            lab_test.test_name = test_name
            lab_test.description = description
            lab_test.result = result
            lab_test.save()

        messages.success(request, "Lab Report Updated Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist, base_models.LabTest.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def add_prescription(request, appointment_id):
    if request.method == 'POST':
        medications = request.POST.get('medications')
        
        Prescription.objects.create(
            appointment_id=appointment_id,
            medications=medications
        )
        messages.success(request, 'Prescription added successfully.')
        return redirect('appointment_detail', appointment_id=appointment_id)
    
    return render(request, 'doctor/add_prescription.html', {'appointment_id': appointment_id})

@login_required
def edit_prescription(request, appointment_id, prescription_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        prescription = base_models.Prescription.objects.get(id=prescription_id)

        if request.method == "POST":
            medications = request.POST.get("medications")
            prescription.medications = medications
            prescription.save()

        messages.success(request, "Prescription Updated Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist, base_models.Prescription.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def payments(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        payments = base_models.Billing.objects.filter(appointment__doctor=doctor)

        context = {
            "payments": payments
        }

        return render(request, "doctor/payments.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def notifications(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        notifications = doctor_models.Notification.objects.filter(doctor=doctor).order_by('-date')

        context = {
            "notifications": notifications
        }

        return render(request, "doctor/notifications.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def mark_noti_seen(request, noti_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        notification = doctor_models.Notification.objects.get(doctor=doctor, id=noti_id)
        notification.seen = True
        notification.save()
        
        messages.success(request, "Notification marked as seen")
        return redirect("doctor:notifications")
    except (doctor_models.Doctor.DoesNotExist, doctor_models.Notification.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def profile(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        
        if request.method == "POST":
            full_name = request.POST.get("full_name")
            image = request.FILES.get("image")
            mobile = request.POST.get("mobile")
            country = request.POST.get("country")
            bio = request.POST.get("bio")
            specialization = request.POST.get("specialization")
            qualifications = request.POST.get("qualifications")
            years_of_experience = request.POST.get("years_of_experience")

            doctor.full_name = full_name
            doctor.mobile = mobile
            doctor.country = country
            doctor.bio = bio
            doctor.specialization = specialization
            doctor.qualifications = qualifications
            doctor.years_of_experience = years_of_experience

            if image != None:
                doctor.image = image

            doctor.save()
            messages.success(request, "Profile updated successfully")
            return redirect("doctor:profile")

        context = {
            "doctor": doctor
        }

        return render(request, "doctor/profile.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def clear_notifications(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        doctor_models.Notification.objects.filter(doctor=doctor).delete()
        messages.success(request, "All notifications have been cleared")
        return redirect("doctor:notifications")
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def reschedule_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        if request.method == "POST":
            new_date = request.POST.get("new_date")
            new_time = request.POST.get("new_time")
            
            start_time = new_time.split(" - ")[0]
            appointment_datetime = f"{new_date} {start_time}:00"
            
            appointment.appointment_date = appointment_datetime
            appointment.save()

            messages.success(request, "Appointment rescheduled successfully.")
            return redirect("doctor:appointment_detail", appointment.appointment_id)
        
        context = {
            "appointment": appointment
        }
        return render(request, "doctor/reschedule_appointment.html", context)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def doctor_list(request):
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, 'Please login to view doctors.')
        return redirect('login')
    
    # Get filter parameters
    filters = {
        'specialty': request.GET.get('specialty'),
        'name': request.GET.get('name')
    }
    
    # Get doctors from API
    response = APIService.get_doctors(filters, token)
    if response.get('success'):
        doctors = response['doctors']
    else:
        doctors = []
        messages.error(request, response.get('message', 'Failed to load doctors.'))
    
    return render(request, 'doctor/doctor_list.html', {
        'doctors': doctors,
        'specialties': response.get('specialties', [])
    })

@login_required
def doctor_detail(request, doctor_id):
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, 'Please login to view doctor details.')
        return redirect('login')
    
    # Get doctor details from API
    response = APIService.get_doctor(doctor_id, token)
    if response.get('success'):
        doctor = response['doctor']
    else:
        messages.error(request, response.get('message', 'Failed to load doctor details.'))
        return redirect('doctor_list')
    
    # Get available slots if date is provided
    date = request.GET.get('date')
    available_slots = []
    if date:
        slots_response = APIService.get_available_slots(doctor_id, date, token)
        if slots_response.get('success'):
            available_slots = slots_response['slots']
    
    return render(request, 'doctor/doctor_detail.html', {
        'doctor': doctor,
        'available_slots': available_slots,
        'selected_date': date
    })

@login_required
def book_appointment(request, doctor_id):
    if request.method == "POST":
        token = request.session.get('token')
        if not token:
            messages.error(request, "Authentication required")
            return redirect('userauths:sign-in')
        
        data = {
            'doctor_id': doctor_id,
            'appointment_date': request.POST.get('appointment_date'),
            'time_slot': request.POST.get('time_slot'),
            'illness': request.POST.get('illness'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'contact': request.POST.get('contact'),
            'age': request.POST.get('age'),
            'gender': request.POST.get('gender')
        }
        
        response = APIService.create_appointment(token, data)
        if response.get('status') == 'success':
            messages.success(request, "Appointment booked successfully!")
            return redirect('doctor:appointment-list')
        else:
            messages.error(request, response.get('message', 'Failed to book appointment'))
    
    token = request.session.get('token')
    response = APIService.get_doctor(doctor_id, token)
    if response.get('status') == 'success':
        doctor = response.get('doctor')
        return render(request, "doctor/book-appointment.html", {"doctor": doctor})
    else:
        messages.error(request, response.get('message', 'Failed to fetch doctor details'))
        return redirect('doctor:doctor-list')

@login_required
def appointment_list(request):
    token = request.session.get('token')
    if not token:
        messages.error(request, "Authentication required")
        return redirect('userauths:sign-in')
    
    response = APIService.get_appointments(token)
    if response.get('status') == 'success':
        appointments = response.get('appointments', [])
        return render(request, "doctor/appointment-list.html", {"appointments": appointments})
    else:
        messages.error(request, response.get('message', 'Failed to fetch appointments'))
        return redirect('base:index')
