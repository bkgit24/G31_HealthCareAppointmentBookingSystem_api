"""
Model mappings between Flask and Django models.
This file contains the field mappings and translation logic for data synchronization.
"""

# Model name mappings
FLASK_TO_DJANGO_MODEL_MAPPING = {
    # Model name mappings
    'FlaskUser': 'User',
    'FlaskDoctor': 'Doctor',
    'FlaskPatient': 'Patient',
    'FlaskAppointment': 'Appointment',
    
    # Field name mappings for Doctor model
    'doctor_fields': {
        'id': 'id',
        'user_id': 'user',
        'full_name': 'full_name',
        'profile_image': 'image',
        'mobile': 'mobile',
        'country': 'country',
        'bio': 'bio',
        'specialization': 'specialization',
        'qualifications': 'qualifications',
        'years_of_experience': 'years_of_experience',
        'next_available_appointment_date': 'next_available_appointment_date'
    },
    
    # Field name mappings for Patient model
    'patient_fields': {
        'id': 'id',
        'user_id': 'user',
        'profile_picture': 'image',
        'full_name': 'full_name',
        'email': 'email',
        'mobile': 'mobile',
        'address': 'address',
        'gender': 'gender',
        'date_of_birth': 'dob',
        'blood_group': 'blood_group'
    },
    
    # Field name mappings for Appointment model
    'appointment_fields': {
        'id': 'appointment_id',
        'service_id': 'service',
        'doctor_id': 'doctor',
        'patient_id': 'patient',
        'appointment_date': 'appointment_date',
        'issues': 'issues',
        'symptoms': 'symptoms',
        'status': 'status'
    },
    
    # Field name mappings for user registration
    'user_registration_fields': {
        'full_name': 'full_name',
        'email': 'email',
        'password': 'password1'
    }
}

def translate_flask_to_django(flask_data, model_type):
    """
    Convert Flask API response to Django model format
    """
    django_data = {}
    
    if model_type not in ['doctor', 'patient', 'appointment']:
        raise ValueError(f"Invalid model type: {model_type}")
    
    field_mapping = FLASK_TO_DJANGO_MODEL_MAPPING[f'{model_type}_fields']
    
    for flask_field, django_field in field_mapping.items():
        if flask_field in flask_data:
            django_data[django_field] = flask_data[flask_field]
    
    return django_data

def translate_django_to_flask(django_data, model_type):
    """
    Convert Django model data to Flask API format
    """
    flask_data = {}
    
    if model_type not in ['doctor', 'patient', 'appointment', 'user_registration']:
        raise ValueError(f"Invalid model type: {model_type}")
    
    field_mapping = FLASK_TO_DJANGO_MODEL_MAPPING.get(f'{model_type}_fields')
    if not field_mapping:
        raise ValueError(f"No field mapping found for model type: {model_type}")
    reverse_mapping = {v: k for k, v in field_mapping.items()}
    
    for django_field, flask_field in reverse_mapping.items():
        if django_field in django_data:
            flask_data[flask_field] = django_data[django_field]
    
    return flask_data 