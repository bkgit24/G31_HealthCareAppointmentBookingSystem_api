import requests
from django.conf import settings
import json
from datetime import datetime
from .model_mappings import translate_flask_to_django, translate_django_to_flask
import logging
import re

logger = logging.getLogger('api_service')

def _sanitize_query_param(value):
    # Only allow alphanumeric, dash, underscore, and space
    if isinstance(value, str):
        return re.sub(r'[^\w\-\s]', '', value)
    return value

def _validate_jwt_token(token):
    if not token or not isinstance(token, str):
        return False
    # Basic JWT format: header.payload.signature
    return bool(re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$', token))

class APIService:
    BASE_URL = getattr(settings, 'FLASK_API_URL', 'http://localhost:5000/api').rstrip('/')  # Remove trailing slash
    TIMEOUT = 10  # seconds

    @staticmethod
    def get_headers(jwt_token=None):
        headers = {'Content-Type': 'application/json'}
        if jwt_token:
            if not _validate_jwt_token(jwt_token):
                logger.error('Invalid JWT token format')
                raise ValueError('Invalid JWT token format')
            headers['Authorization'] = f'Bearer {jwt_token}'
        return headers

    @staticmethod
    def _handle_response(response):
        try:
            content_type = response.headers.get('Content-Type', '')
            if response.status_code in (401, 403):
                logger.error(f"Authentication/Authorization failed: {response.text}")
                return {'error': 'Authentication/Authorization failed'}
            if response.status_code >= 500:
                logger.error(f"Server error: {response.text}")
                return {'error': 'Server error'}
            if 'application/json' in content_type:
                data = response.json()
            else:
                logger.error(f"Unexpected content type: {content_type}")
                return {'error': 'Unexpected content type'}
            response.raise_for_status()
            return data
        except requests.exceptions.Timeout:
            logger.error('Request timed out')
            return {'error': 'Request timed out'}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {str(e)} | Response: {getattr(response, 'text', '')}")
            return {'error': f'HTTP error: {str(e)}'}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            return {'error': 'Invalid response from server'}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}'}
        finally:
            try:
                response.close()
            except Exception:
                pass

    @staticmethod
    def login(email, password):
        url = f"{APIService.BASE_URL}/login/"
        payload = json.dumps({'email': email, 'password': password})
        try:
            response = requests.post(url, data=payload, headers=APIService.get_headers(), timeout=APIService.TIMEOUT)
            return APIService._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {str(e)}")
            return {'error': f'Authentication failed: {str(e)}'}

    @staticmethod
    def register(user_data):
        url = f"{APIService.BASE_URL}/register/"
        payload = json.dumps(user_data)
        try:
            response = requests.post(url, data=payload, headers=APIService.get_headers(), timeout=APIService.TIMEOUT)
            return APIService._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Register request failed: {str(e)}")
            return {'error': f'Registration failed: {str(e)}'}

    @staticmethod
    def get_doctors(filters=None, jwt_token=None):
        url = f"{APIService.BASE_URL}/doctors/"
        if filters:
            query_params = '&'.join([
                f"{_sanitize_query_param(key)}={_sanitize_query_param(value)}"
                for key, value in filters.items() if value
            ])
            url = f"{url}?{query_params}"
        try:
            response = requests.get(url, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            data = APIService._handle_response(response)
            if 'error' in data:
                return data
            if 'doctors' in data:
                data['doctors'] = [translate_flask_to_django(doctor, 'doctor') for doctor in data['doctors']]
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Get doctors request failed: {str(e)}")
            return {'error': f'Failed to get doctors: {str(e)}'}

    @staticmethod
    def get_doctor(doctor_id, jwt_token=None):
        url = f"{APIService.BASE_URL}/doctors/{doctor_id}/"
        try:
            response = requests.get(url, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            data = APIService._handle_response(response)
            if 'doctor' in data:
                data['doctor'] = translate_flask_to_django(data['doctor'], 'doctor')
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Get doctor request failed: {str(e)}")
            return {'error': f'Failed to get doctor: {str(e)}'}

    @staticmethod
    def get_appointments(filters=None, jwt_token=None):
        url = f"{APIService.BASE_URL}/appointments/"
        if filters:
            query_params = '&'.join([
                f"{_sanitize_query_param(key)}={_sanitize_query_param(value)}"
                for key, value in filters.items() if value
            ])
            url = f"{url}?{query_params}"
        try:
            response = requests.get(url, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            data = APIService._handle_response(response)
            if 'appointments' in data:
                data['appointments'] = [translate_flask_to_django(appt, 'appointment') for appt in data['appointments']]
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Get appointments request failed: {str(e)}")
            return {'error': f'Failed to get appointments: {str(e)}'}

    @staticmethod
    def get_appointment(appointment_id, jwt_token=None):
        url = f"{APIService.BASE_URL}/appointments/{appointment_id}/"
        try:
            response = requests.get(url, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            data = APIService._handle_response(response)
            if 'appointment' in data:
                data['appointment'] = translate_flask_to_django(data['appointment'], 'appointment')
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Get appointment request failed: {str(e)}")
            return {'error': f'Failed to get appointment: {str(e)}'}

    @staticmethod
    def create_appointment(appointment_data, jwt_token=None):
        url = f"{APIService.BASE_URL}/appointments/"
        flask_appointment_data = translate_django_to_flask(appointment_data, 'appointment')
        payload = json.dumps(flask_appointment_data)
        try:
            response = requests.post(url, data=payload, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            data = APIService._handle_response(response)
            if 'appointment' in data:
                data['appointment'] = translate_flask_to_django(data['appointment'], 'appointment')
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Create appointment request failed: {str(e)}")
            return {'error': f'Failed to create appointment: {str(e)}'}

    @staticmethod
    def update_appointment(appointment_id, appointment_data, jwt_token=None):
        url = f"{APIService.BASE_URL}/appointments/{appointment_id}/"
        flask_appointment_data = translate_django_to_flask(appointment_data, 'appointment')
        payload = json.dumps(flask_appointment_data)
        try:
            response = requests.put(url, data=payload, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            data = APIService._handle_response(response)
            if 'appointment' in data:
                data['appointment'] = translate_flask_to_django(data['appointment'], 'appointment')
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Update appointment request failed: {str(e)}")
            return {'error': f'Failed to update appointment: {str(e)}'}

    @staticmethod
    def delete_appointment(appointment_id, jwt_token=None):
        url = f"{APIService.BASE_URL}/appointments/{appointment_id}/"
        try:
            response = requests.delete(url, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            return APIService._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Delete appointment request failed: {str(e)}")
            return {'error': f'Failed to delete appointment: {str(e)}'}

    @staticmethod
    def get_available_slots(doctor_id, date, jwt_token=None):
        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            logger.error('Invalid date format for available slots. Use YYYY-MM-DD.')
            return {'error': 'Invalid date format. Use YYYY-MM-DD.'}
        url = f"{APIService.BASE_URL}/doctors/{doctor_id}/slots"
        params = {'date': date}
        try:
            response = requests.get(url, params=params, headers=APIService.get_headers(jwt_token), timeout=APIService.TIMEOUT)
            return APIService._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Get available slots request failed: {str(e)}")
            return {'error': f'Failed to get available slots: {str(e)}'} 