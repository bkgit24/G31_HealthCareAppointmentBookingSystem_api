from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import datetime
from django.utils import timezone
from decimal import Decimal

import requests
import stripe

from base import models as base_models
from doctor import models as doctor_models
from patient import models as patient_models

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
    try:
        service = base_models.Service.objects.get(id=service_id)
        doctor = doctor_models.Doctor.objects.get(id=doctor_id)
        patient = patient_models.Patient.objects.get(user=request.user)

        time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(9, 18)]

        if request.method == "POST":
            full_name = request.POST.get("full_name")
            email = request.POST.get("email")
            mobile = request.POST.get("mobile")
            gender = request.POST.get("gender")
            address = request.POST.get("address")
            dob = request.POST.get("dob")
            issues = request.POST.get("issues")
            symptoms = request.POST.get("symptoms")
            appointment_date = request.POST.get("appointment_date")
            time_slot = request.POST.get("time_slot")

            start_time = time_slot.split(" - ")[0]
            appointment_datetime = f"{appointment_date} {start_time}"
            
            patient.full_name = full_name
            patient.email = email
            patient.mobile = mobile
            patient.gender = gender
            patient.address = address
            if dob:
                patient.dob = datetime.strptime(dob, '%Y-%m-%d').date()
            patient.save()

            appointment = base_models.Appointment.objects.create(
                service=service,
                doctor=doctor,
                patient=patient,
                appointment_date=appointment_datetime,
                issues=issues,
                symptoms=symptoms,
                status="Scheduled"
            )

            billing = base_models.Billing.objects.create(
                patient=patient,
                appointment=appointment,
                sub_total=appointment.service.cost,
                tax=appointment.service.cost * Decimal('0.05'),
                total=appointment.service.cost * Decimal('1.05'),
                status="Unpaid"
            )

            return redirect("base:checkout", billing.billing_id)

        context = {
            "service": service,
            "doctor": doctor,
            "patient": patient,
            "time_slots": time_slots,
            "today": datetime.now().date(),
        }
        return render(request, "base/book_appointment.html", context)
    except Exception as e:
        return redirect('base:index')

@login_required
def checkout(request, billing_id):
    try:
        billing = base_models.Billing.objects.get(billing_id=billing_id)
        context = {
            "billing": billing,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
            "paypal_client_id": settings.PAYPAL_CLIENT_ID,
        }
        return render(request, "base/checkout.html", context)
    except Exception as e:
        return redirect('index')

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
    return render(request, "base/about.html")

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
