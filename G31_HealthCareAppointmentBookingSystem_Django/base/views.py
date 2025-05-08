from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages

import requests
import stripe
import time

from base import models as base_models
from doctor import models as doctor_models
from patient import models as patient_models
from base.api_service import APIService
from base.model_mappings import translate_django_to_flask

def index(request):
    services = base_models.Service.objects.all()
    context = {"services": services}
    return render(request, "base/index.html", context)

def service_detail(request, service_id):
    service = base_models.Service.objects.get(id=service_id)
    context = {"service": service}
    return render(request, "base/service_detail.html", context)

@login_required
def book_appointment(request, service_id, doctor_id):
    # Always generate time_slots first
    time_slots = {}
    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("18:00", "%H:%M")
    slot_length = timedelta(minutes=30)
    while start_time < end_time:
        slot_start = start_time.strftime("%H:%M")
        slot_end = (start_time + slot_length).strftime("%H:%M")
        value = f"{slot_start}-{slot_end}"
        label = f"{start_time.strftime('%I:%M %p')} - {(start_time + slot_length).strftime('%I:%M %p')}"
        time_slots[value] = label
        start_time += slot_length

    try:
        service = base_models.Service.objects.get(id=service_id)
        doctor = doctor_models.Doctor.objects.get(id=doctor_id)
        patient = patient_models.Patient.objects.get(user=request.user)

        if request.method == "POST":
            print("DEBUG POST DATA:", request.POST)
            try:
                # Get JWT token from session
                jwt_token = request.session.get('jwt_token')
                if not jwt_token:
                    messages.error(request, "Authentication required")
                    return redirect('userauths:sign-in')

                # Prepare data for Flask API
                flask_appointment_data = {
                    'doctor_id': doctor.id,
                    'appointment_date': request.POST.get('appointment_date'),
                    'time_slot': request.POST.get('time_slot'),
                    'illness': request.POST.get('illness'),
                    'first_name': request.POST.get('first_name'),
                    'last_name': request.POST.get('last_name'),
                    'contact': request.POST.get('contact'),
                    'age': request.POST.get('age'),
                    'gender': request.POST.get('gender')
                }

                # Validate required fields
                required_fields = ['doctor_id', 'appointment_date', 'time_slot', 'illness', 
                                 'first_name', 'last_name', 'contact', 'age', 'gender']
                missing_fields = [field for field in required_fields if not flask_appointment_data.get(field)]
                
                if missing_fields:
                    messages.error(request, f"Missing required fields: {', '.join(missing_fields)}")
                    context = {
                        "error": f"Missing required fields: {', '.join(missing_fields)}",
                        "service": service,
                        "doctor": doctor,
                        "patient": patient,
                        "time_slots": time_slots,
                        "today": datetime.now().date(),
                        "post_data": request.POST,
                    }
                    return render(request, "base/book_appointment.html", context)

                # Update patient information
                patient.full_name = f"{flask_appointment_data['first_name']} {flask_appointment_data['last_name']}"
                patient.email = request.POST.get('email')
                patient.mobile = flask_appointment_data['contact']
                patient.gender = flask_appointment_data['gender']
                patient.address = request.POST.get('address')
                patient.save()

                # Create appointment in Django
                appointment_datetime = f"{flask_appointment_data['appointment_date']} {flask_appointment_data['time_slot'].split('-')[0].strip()}"
                appointment = base_models.Appointment.objects.create(
                    service=service,
                    doctor=doctor,
                    patient=patient,
                    appointment_date=appointment_datetime,
                    issues=flask_appointment_data['illness'],
                    symptoms=request.POST.get('symptoms'),
                    status="Scheduled"
                )

                # Send to Flask API with retries
                max_retries = 3
                retry_count = 0
                last_error = None

                while retry_count < max_retries:
                    flask_response = APIService.create_appointment(flask_appointment_data, jwt_token)
                    
                    if 'error' not in flask_response:
                        break
                        
                    last_error = flask_response['error']
                    retry_count += 1
                    
                    if 'database is locked' in last_error.lower():
                        # Wait before retrying
                        time.sleep(0.5 * retry_count)
                        continue
                    else:
                        # For other errors, don't retry
                        break

                if 'error' in flask_response:
                    print(f"Flask API error after {retry_count} retries: {last_error}")
                    messages.error(request, f"Failed to sync with API: {last_error}")
                    return redirect('base:book_appointment', service_id=service.id, doctor_id=doctor.id)

                # Create billing
                billing = base_models.Billing.objects.create(
                    patient=patient,
                    appointment=appointment,
                    sub_total=appointment.service.cost,
                    tax=appointment.service.cost * Decimal('0.05'),
                    total=appointment.service.cost * Decimal('1.05'),
                    status="Unpaid"
                )

                messages.success(request, "Appointment booked successfully!")
                return redirect(reverse("base:checkout", args=[billing.billing_id]))

            except Exception as post_e:
                print(f"Error in POST: {str(post_e)}")
                context = {
                    "error": f"POST ERROR: {str(post_e)}",
                    "service": service,
                    "doctor": doctor,
                    "patient": patient,
                    "time_slots": time_slots,
                    "today": datetime.now().date(),
                    "post_data": request.POST,
                }
                return render(request, "base/book_appointment.html", context)

        context = {
            "service": service,
            "doctor": doctor,
            "patient": patient,
            "time_slots": time_slots,
            "today": datetime.now().date(),
        }
        return render(request, "base/book_appointment.html", context)
    except Exception as e:
        print(f"Error in view: {str(e)}")
        context = {
            "error": str(e),
            "service": service if 'service' in locals() else None,
            "doctor": doctor if 'doctor' in locals() else None,
            "patient": patient if 'patient' in locals() else None,
            "time_slots": time_slots,
        }
        return render(request, "base/book_appointment.html", context)

@login_required
def checkout(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        context = {
            "billing": billing,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
        }
        return render(request, "base/checkout.html", context)
    except Exception as e:
        return redirect('base:index')

@csrf_exempt
def stripe_payment(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        stripe.api_key = settings.STRIPE_SECRET_KEY

        checkout_session = stripe.checkout.Session.create(
            customer_email=billing.patient.email,
            payment_method_types=['card'],
            line_items = [
                {
                    'price_data': {
                        'currency': 'USD',
                        'product_data': {
                            'name': billing.patient.full_name
                        },
                        'unit_amount': int(billing.total * 100)
                    },
                    'quantity': 1
                }
            ],
            mode='payment',
            success_url = request.build_absolute_uri(reverse("base:stripe_payment_verify", args=[billing.billing_id])) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("base:stripe_payment_verify", args=[billing.billing_id])) + "?session_id={CHECKOUT_SESSION_ID}"
        )
        return JsonResponse({"sessionId": checkout_session.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def stripe_payment_verify(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        session_id = request.GET.get("session_id")
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            if billing.status == "Unpaid":
                billing.status = "Paid"
                billing.save()
                billing.appointment.status = "Completed"
                billing.appointment.save()

                doctor_models.Notification.objects.create(
                    doctor=billing.appointment.doctor,
                    appointment=billing.appointment,
                    type="New Appointment"
                )

                patient_models.Notification.objects.create(
                    patient=billing.appointment.patient,
                    appointment=billing.appointment,
                    type="Appointment Scheduled"
                )

                return redirect(reverse('base:payment_status', args=[billing.billing_id]) + '?payment_status=paid')
        return redirect(reverse('base:payment_status', args=[billing.billing_id]) + '?payment_status=failed')
    except Exception as e:
        return redirect('index')

def get_paypal_access_token():
    try:
        token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
        data = {'grant_type': 'client_credentials'}
        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET_ID)
        response = requests.post(token_url, data=data, auth=auth)

        if response.status_code == 200:
            return response.json()['access_token']
        raise Exception(f"Failed to get access token from PayPal. Status code: {response.status_code}")
    except Exception as e:
        raise Exception(f"PayPal authentication failed: {str(e)}")

def paypal_payment_verify(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        transaction_id = request.GET.get("transaction_id")
        paypal_api_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{transaction_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {get_paypal_access_token()}'
        }

        response = requests.get(paypal_api_url, headers=headers)

        if response.status_code == 200:
            paypal_order_data = response.json()
            paypal_payment_status = paypal_order_data['status']

            if paypal_payment_status == "COMPLETED":
                if billing.status == "Unpaid":
                    billing.status = "Paid"
                    billing.save()
                    billing.appointment.status = "Completed"
                    billing.appointment.save()

                    doctor_models.Notification.objects.create(
                        doctor=billing.appointment.doctor,
                        appointment=billing.appointment,
                        type="New Appointment"
                    )

                    patient_models.Notification.objects.create(
                        patient=billing.appointment.patient,
                        appointment=billing.appointment,
                        type="Appointment Scheduled"
                    )

                    merge_data = {"billing": billing}
                    
                    subject = "New Appointment"
                    text_body = render_to_string("email/new_appointment.txt", merge_data)
                    html_body = render_to_string("email/new_appointment.html", merge_data)
                    
                    try:
                        msg = EmailMultiAlternatives(
                            subject=subject,
                            from_email=settings.FROM_EMAIL,
                            to=[billing.appointment.doctor.user.email],
                            body=text_body
                        )
                        msg.attach_alternative(html_body, "text/html")
                        msg.send()

                        subject = "Appointment Booked Successfully"
                        text_body = render_to_string("email/appointment_booked.txt", merge_data)
                        html_body = render_to_string("email/appointment_booked.html", merge_data)

                        msg = EmailMultiAlternatives(
                            subject=subject,
                            from_email=settings.FROM_EMAIL,
                            to=[billing.appointment.patient.email],
                            body=text_body
                        )
                        msg.attach_alternative(html_body, "text/html")
                        msg.send()
                    except Exception as e:
                        pass

                    return redirect(reverse('base:payment_status', args=[billing.billing_id]) + '?payment_status=paid')
        return redirect(reverse('base:payment_status', args=[billing.billing_id]) + '?payment_status=failed')
    except Exception as e:
        return redirect('index')

@login_required
def payment_status(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        payment_status = request.GET.get("payment_status")
        context = {
            "billing": billing,
            "payment_status": payment_status
        }
        return render(request, "base/payment_status.html", context)
    except Exception as e:
        return redirect('index')

def testimonials(request):
    return render(request, "base/testimonials.html")

def about(request):
    return render(request, "base/pages/about.html")

@login_required
def test_payment_verify(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        billing.status = "Paid"
        billing.save()
        billing.appointment.status = "Completed"
        billing.appointment.save()

        doctor_models.Notification.objects.create(
            doctor=billing.appointment.doctor,
            appointment=billing.appointment,
            type="New Appointment"
        )

        patient_models.Notification.objects.create(
            patient=billing.appointment.patient,
            appointment=billing.appointment,
            type="Appointment Scheduled"
        )

        return redirect(reverse('base:payment_status', args=[billing.billing_id]) + '?payment_status=paid')
    except Exception as e:
        return redirect('index')
