from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from datetime import datetime
from django.urls import reverse

from base import models as base_models
from patient import models as patient_models
from doctor import models as doctor_models


@login_required
def dashboard(request):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
    except patient_models.Patient.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

    appointments = base_models.Appointment.objects.filter(patient=patient).order_by("-id")
    notifications = patient_models.Notification.objects.filter(patient=patient, seen=False).order_by("-id")

    time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(9, 18)]

    total_spent = base_models.Billing.objects.filter(
        patient=patient,
        status='Paid'
    ).aggregate(total=models.Sum('total'))['total'] or 0

    context = {
        "appointments": appointments[:5],
        "notifications": notifications[:5],
        "total_spent": total_spent,
        "patient": patient,
        "time_slots": time_slots,
        "today": datetime.now().date(),
    }
    return render(request, "patient/dashboard.html", context)


@login_required
def appointments(request):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        appointments = base_models.Appointment.objects.filter(patient=patient)

        context = {
            "appointments": appointments,
        }

        return render(request, "patient/appointments.html", context)
    except patient_models.Patient.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def appointment_detail(request, appointment_id):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, patient=patient)
        
        medical_records = base_models.MedicalRecord.objects.filter(appointment=appointment)
        lab_tests = base_models.LabTest.objects.filter(appointment=appointment)
        prescriptions = base_models.Prescription.objects.filter(appointment=appointment)

        context = {
            "appointment": appointment,
            "medical_records": medical_records,
            "lab_tests": lab_tests,
            "prescriptions": prescriptions,
        }

        return render(request, "patient/appointment_detail.html", context)
    except (patient_models.Patient.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def cancel_appointment(request, appointment_id):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, patient=patient)

        appointment.status = "Cancelled"
        appointment.save()
        
        patient_models.Notification.objects.create(
            patient=patient,
            appointment=appointment,
            type="Appointment Cancelled"
        )

        doctor_models.Notification.objects.create(
            doctor=appointment.doctor,
            appointment=appointment,
            type="Appointment Cancelled"
        )

        messages.success(request, "Appointment Cancelled Successfully")
        return redirect("patient:appointment_detail", appointment.appointment_id)
    except (patient_models.Patient.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def activate_appointment(request, appointment_id):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, patient=patient)

        appointment.status = "Scheduled"
        appointment.save()
        
        patient_models.Notification.objects.create(
            patient=patient,
            appointment=appointment,
            type="Appointment Scheduled"
        )

        doctor_models.Notification.objects.create(
            doctor=appointment.doctor,
            appointment=appointment,
            type="New Appointment"
        )

        messages.success(request, "Appointment Re-Scheduled Successfully")
        return redirect("patient:appointment_detail", appointment.appointment_id)
    except (patient_models.Patient.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def complete_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(base_models.Appointment, appointment_id=appointment_id, patient=request.user.patient)
        if appointment.status == "Scheduled":
            appointment.status = "Completed"
            appointment.save()
            
            doctor_models.Notification.objects.create(
                doctor=appointment.doctor,
                appointment=appointment,
                type="Appointment Completed"
            )
            
            patient_models.Notification.objects.create(
                patient=appointment.patient,
                appointment=appointment,
                type="Appointment Completed"
            )
            
            messages.success(request, "Appointment marked as completed successfully.")
            return redirect('patient:appointment_detail', appointment_id=appointment_id)
        return redirect('patient:appointment_detail', appointment_id=appointment_id)
    except (patient_models.Patient.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def payments(request):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        payments = base_models.Billing.objects.filter(appointment__patient=patient)

        context = {
            "payments": payments,
        }

        return render(request, "patient/payments.html", context)
    except patient_models.Patient.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def notifications(request):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        notifications = patient_models.Notification.objects.filter(patient=patient).order_by('-date')

        context = {
            "notifications": notifications
        }

        return render(request, "patient/notifications.html", context)
    except patient_models.Patient.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def mark_noti_seen(request, id):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        notification = patient_models.Notification.objects.get(patient=patient, id=id)
        notification.seen = True
        notification.save()
        
        messages.success(request, "Notification marked as seen")
        return redirect("patient:notifications")
    except (patient_models.Patient.DoesNotExist, patient_models.Notification.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def clear_notifications(request):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        patient_models.Notification.objects.filter(patient=patient).delete()
        messages.success(request, "All notifications have been cleared")
        return redirect("patient:notifications")
    except patient_models.Patient.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def profile(request):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        formatted_dob = patient.dob.strftime('%Y-%m-%d')
        
        if request.method == "POST":
            full_name = request.POST.get("full_name")
            image = request.FILES.get("image")
            mobile = request.POST.get("mobile")
            address = request.POST.get("address")
            gender = request.POST.get("gender")
            dob = request.POST.get("dob")
            blood_group = request.POST.get("blood_group")

            patient.full_name = full_name
            patient.mobile = mobile
            patient.address = address
            patient.gender = gender
            patient.dob = dob
            patient.blood_group = blood_group

            if image != None:
                patient.image = image

            patient.save()
            messages.success(request, "Profile updated successfully")
            return redirect("patient:profile")

        context = {
            "patient": patient,
            "formatted_dob": formatted_dob,
        }

        return render(request, "patient/profile.html", context)
    except patient_models.Patient.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')


@login_required
def reschedule_appointment(request, appointment_id):
    try:
        patient = patient_models.Patient.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, patient=patient)

        if request.method == "POST":
            new_date = request.POST.get("new_date")
            new_time = request.POST.get("new_time")
            
            start_time = new_time.split(" - ")[0]
            appointment_datetime = f"{new_date} {start_time}:00"
            
            appointment.appointment_date = appointment_datetime
            appointment.save()

            messages.success(request, "Appointment rescheduled successfully.")
            return redirect("patient:appointment_detail", appointment.appointment_id)
        
        context = {
            "appointment": appointment
        }
        return render(request, "patient/reschedule_appointment.html", context)
    except (patient_models.Patient.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')
