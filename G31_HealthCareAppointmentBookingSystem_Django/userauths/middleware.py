from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class RoleSelectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None

        if request.user.is_superuser or request.user.is_staff:
            return None

        allowed_paths = [
            reverse('userauths:select-role'),
            reverse('userauths:sign-out'),
        ]

        if request.path.startswith('/accounts/'):
            return None

        # Only redirect if user has no role and google_signup flag is set
        if (
            not getattr(request.user, 'user_type', None)
            and request.session.get('google_signup')
            and request.path not in allowed_paths
        ):
            return redirect('userauths:select-role')

        # If user has a role but tries to access select-role, redirect to dashboard
        if getattr(request.user, 'user_type', None) and request.path == reverse('userauths:select-role'):
            redirect_url = getattr(settings, 'LOGIN_REDIRECT_URL', '/')
            return redirect(redirect_url)

        return None 