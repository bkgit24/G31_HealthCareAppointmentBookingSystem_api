from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, LoginForm
from base.api_service import APIService
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import SelectRoleForm
from .models import USER_TYPE, User
from base.model_mappings import translate_django_to_flask
from django.conf import settings

from doctor import models as doctor_models
from patient import models as patient_models

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Set _raw_password for signal to use
            user = form.save(commit=False)
            user._raw_password = form.cleaned_data['password1']
            user_type = form.cleaned_data.get('user_type')
            user.user_type = user_type
            user.save()
            form.save_m2m()
            # Automatically create Doctor or Patient profile
            full_name = form.cleaned_data.get('full_name') or user.username or user.email
            if user_type == 'Doctor':
                doctor_models.Doctor.objects.get_or_create(user=user, defaults={'full_name': full_name})
            elif user_type == 'Patient':
                patient_models.Patient.objects.get_or_create(user=user, defaults={'full_name': full_name, 'email': user.email})
            # Map Django form data to Flask API registration format
            flask_user_data = translate_django_to_flask(form.cleaned_data, 'user_registration')
            response = APIService.register(flask_user_data)
            if response.get('status') == 'success':
                messages.success(request, 'Registration successful. Please login.')
                return redirect('userauths:sign-in')
            else:
                # Show the full error message from the API for debugging
                messages.error(request, f"Registration failed: {response}")
    else:
        form = UserRegisterForm()
    
    return render(request, 'userauths/sign-up.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            response = APIService.login(
                form.cleaned_data['email'],
                form.cleaned_data['password']
            )
            if response.get('status') == 'success':
                # Store JWT token in session
                request.session['jwt_token'] = response.get('access_token')
                # Get user info from API response
                user_info = response.get('user')
                if user_info:
                    User = get_user_model()
                    user, created = User.objects.get_or_create(email=user_info['email'], defaults={'username': user_info['email']})
                    # Sync user_type from Flask backend
                    if 'role' in user_info:
                        user.user_type = user_info['role'].capitalize()  # 'doctor' -> 'Doctor'
                        user.save()
                    backend = settings.AUTHENTICATION_BACKENDS[0]
                    login(request, user, backend=backend)
                messages.success(request, 'Login successful.')
                return redirect('/')
            else:
                messages.error(request, response.get('message', 'Login failed.'))
    else:
        form = LoginForm()
    
    return render(request, 'userauths/sign-in.html', {'form': form})

def logout_view(request):
    # Clear JWT token from session
    request.session.pop('jwt_token', None)
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('/')

@login_required
def profile_view(request):
    token = request.session.get('jwt_token')
    if not token:
        messages.error(request, 'Please login to view your profile.')
        return redirect('userauths:sign-in')
    
    # Get user profile from API
    response = APIService.get_current_user(token)
    if response.get('success'):
        return render(request, 'userauths/profile.html', {'profile': response['user']})
    else:
        messages.error(request, response.get('message', 'Failed to load profile.'))
        return redirect('dashboard')

class SelectRoleView(LoginRequiredMixin, FormView):
    template_name = 'userauths/select_role.html'
    form_class = SelectRoleForm
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        # Only allow access if user came from Google signup
        if not request.session.get('google_signup'):
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        selected_role = form.cleaned_data['user_type']

        user.user_type = selected_role
        user.save()

        full_name = user.get_full_name() or user.username

        if selected_role == "Doctor":
            doctor_models.Doctor.objects.get_or_create(
                user=user,
                defaults={'full_name': full_name}
            )
            messages.success(self.request, f"Role set to Doctor. Profile created/updated.")
        elif selected_role == "Patient":
            patient_models.Patient.objects.get_or_create(
                user=user,
                defaults={'full_name': full_name, 'email': user.email} # Patient model might need email
            )
            messages.success(self.request, f"Role set to Patient. Profile created/updated.")
        else:
            messages.warning(self.request, "Invalid role selected.")
            return self.form_invalid(form)

        # Clear the google_signup flag after role selection
        self.request.session.pop('google_signup', None)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_roles'] = USER_TYPE
        return context

@login_required
def role_based_redirect(request):
    user = request.user
    if user.user_type == "Doctor":
        return redirect('doctor:dashboard')
    elif user.user_type == "Patient":
        return redirect('patient:dashboard')
    else:
        return redirect('/')
