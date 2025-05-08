from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from doctor.models import Doctor
from patient.models import Patient
from base.models import Appointment
from base.api_service import APIService
import logging
import requests

logger = logging.getLogger('api_service')

class Command(BaseCommand):
    help = 'Synchronize data between Flask and Django models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['doctor', 'patient', 'appointment', 'all'],
            default='all',
            help='Model to synchronize'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Admin username for API authentication'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Admin password for API authentication'
        )
        parser.add_argument(
            '--api-url',
            type=str,
            help='Flask API URL (defaults to settings.FLASK_API_URL)'
        )

    def handle(self, *args, **options):
        # Get admin credentials
        username = options['username']
        password = options['password']
        
        if not username or not password:
            self.stdout.write(self.style.ERROR('Please provide admin username and password'))
            return
        
        # Check if Flask API is accessible
        try:
            api_url = options.get('api_url') or APIService.BASE_URL
            # Try to access the doctors endpoint instead of health check
            response = requests.get(f"{api_url}/doctors")
            if response.status_code == 404:
                self.stdout.write(self.style.ERROR(f'Flask API is not accessible at {api_url}'))
                self.stdout.write(self.style.ERROR('Please ensure the Flask backend is running and the API endpoints are correct'))
                return
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Cannot connect to Flask API at {api_url}'))
            self.stdout.write(self.style.ERROR('Please ensure the Flask backend is running'))
            self.stdout.write(self.style.ERROR(f'Error details: {str(e)}'))
            return
        
        # Login to get JWT token
        login_response = APIService.login(username, password)
        if 'error' in login_response:
            self.stdout.write(self.style.ERROR(f'Authentication failed: {login_response["error"]}'))
            return
        
        if not login_response.get('token'):
            self.stdout.write(self.style.ERROR('Failed to authenticate with API'))
            self.stdout.write(self.style.ERROR('Please check your username and password'))
            return
        
        jwt_token = login_response['token']
        
        # Sync based on model choice
        model = options['model']
        if model in ['doctor', 'all']:
            self.sync_doctors(jwt_token)
        if model in ['patient', 'all']:
            self.sync_patients(jwt_token)
        if model in ['appointment', 'all']:
            self.sync_appointments(jwt_token)
        
        self.stdout.write(self.style.SUCCESS('Data synchronization completed'))

    def sync_doctors(self, jwt_token):
        """Sync doctors from Flask API to Django database"""
        self.stdout.write('Syncing doctors...')
        
        try:
            api_response = APIService.get_doctors(jwt_token=jwt_token)
            doctors = api_response.get('doctors', [])
            
            for flask_doctor in doctors:
                # Get or create user
                user, created = User.objects.get_or_create(
                    username=flask_doctor.get('username'),
                    defaults={
                        'email': flask_doctor.get('email', ''),
                        'first_name': flask_doctor.get('first_name', ''),
                        'last_name': flask_doctor.get('last_name', ''),
                        'user_type': 'Doctor'
                    }
                )
                
                # Get or create doctor
                doctor, created = Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'full_name': flask_doctor.get('full_name', ''),
                        'mobile': flask_doctor.get('mobile', ''),
                        'country': flask_doctor.get('country', ''),
                        'bio': flask_doctor.get('bio', ''),
                        'specialization': flask_doctor.get('specialization', ''),
                        'qualifications': flask_doctor.get('qualifications', ''),
                        'years_of_experience': flask_doctor.get('years_of_experience', '')
                    }
                )
                
                if not created:
                    # Update existing doctor
                    doctor.full_name = flask_doctor.get('full_name', doctor.full_name)
                    doctor.mobile = flask_doctor.get('mobile', doctor.mobile)
                    doctor.country = flask_doctor.get('country', doctor.country)
                    doctor.bio = flask_doctor.get('bio', doctor.bio)
                    doctor.specialization = flask_doctor.get('specialization', doctor.specialization)
                    doctor.qualifications = flask_doctor.get('qualifications', doctor.qualifications)
                    doctor.years_of_experience = flask_doctor.get('years_of_experience', doctor.years_of_experience)
                    doctor.save()
                
                self.stdout.write(f"Synced doctor: {doctor.full_name}")
        
        except Exception as e:
            logger.error(f"Error syncing doctors: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error syncing doctors: {str(e)}'))

    def sync_patients(self, jwt_token):
        """Sync patients from Flask API to Django database"""
        self.stdout.write('Syncing patients...')
        
        try:
            api_response = APIService.get_patients(jwt_token=jwt_token)
            patients = api_response.get('patients', [])
            
            for flask_patient in patients:
                # Get or create user
                user, created = User.objects.get_or_create(
                    username=flask_patient.get('username'),
                    defaults={
                        'email': flask_patient.get('email', ''),
                        'first_name': flask_patient.get('first_name', ''),
                        'last_name': flask_patient.get('last_name', ''),
                        'user_type': 'Patient'
                    }
                )
                
                # Get or create patient
                patient, created = Patient.objects.get_or_create(
                    user=user,
                    defaults={
                        'full_name': flask_patient.get('full_name', ''),
                        'email': flask_patient.get('email', ''),
                        'mobile': flask_patient.get('mobile', ''),
                        'address': flask_patient.get('address', ''),
                        'gender': flask_patient.get('gender', ''),
                        'dob': flask_patient.get('date_of_birth'),
                        'blood_group': flask_patient.get('blood_group', '')
                    }
                )
                
                if not created:
                    # Update existing patient
                    patient.full_name = flask_patient.get('full_name', patient.full_name)
                    patient.email = flask_patient.get('email', patient.email)
                    patient.mobile = flask_patient.get('mobile', patient.mobile)
                    patient.address = flask_patient.get('address', patient.address)
                    patient.gender = flask_patient.get('gender', patient.gender)
                    patient.dob = flask_patient.get('date_of_birth', patient.dob)
                    patient.blood_group = flask_patient.get('blood_group', patient.blood_group)
                    patient.save()
                
                self.stdout.write(f"Synced patient: {patient.full_name}")
        
        except Exception as e:
            logger.error(f"Error syncing patients: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error syncing patients: {str(e)}'))

    def sync_appointments(self, jwt_token):
        """Sync appointments from Flask API to Django database"""
        self.stdout.write('Syncing appointments...')
        
        try:
            api_response = APIService.get_appointments(jwt_token=jwt_token)
            appointments = api_response.get('appointments', [])
            
            for flask_appointment in appointments:
                # Get related models
                doctor = Doctor.objects.filter(user__username=flask_appointment.get('doctor_username')).first()
                patient = Patient.objects.filter(user__username=flask_appointment.get('patient_username')).first()
                
                if not doctor or not patient:
                    logger.warning(f"Skipping appointment: Doctor or patient not found")
                    continue
                
                # Get or create appointment
                appointment, created = Appointment.objects.get_or_create(
                    appointment_id=flask_appointment.get('id'),
                    defaults={
                        'doctor': doctor,
                        'patient': patient,
                        'appointment_date': flask_appointment.get('appointment_date'),
                        'issues': flask_appointment.get('issues', ''),
                        'symptoms': flask_appointment.get('symptoms', ''),
                        'status': flask_appointment.get('status', 'Pending')
                    }
                )
                
                if not created:
                    # Update existing appointment
                    appointment.doctor = doctor
                    appointment.patient = patient
                    appointment.appointment_date = flask_appointment.get('appointment_date', appointment.appointment_date)
                    appointment.issues = flask_appointment.get('issues', appointment.issues)
                    appointment.symptoms = flask_appointment.get('symptoms', appointment.symptoms)
                    appointment.status = flask_appointment.get('status', appointment.status)
                    appointment.save()
                
                self.stdout.write(f"Synced appointment: {appointment.appointment_id}")
        
        except Exception as e:
            logger.error(f"Error syncing appointments: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error syncing appointments: {str(e)}')) 