from django import forms
from .models import Appointment

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'issues', 'status']  # Add other fields as needed
        widgets = {
            'appointment_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control form-control-lg', 'placeholder': 'Select date and time'}),
            'issues': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 5, 'placeholder': 'Describe your issue'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-lg'}),
        } 