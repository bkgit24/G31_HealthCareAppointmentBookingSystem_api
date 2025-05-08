from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get JWT token from session
        token = request.session.get('jwt_token')
        if token:
            # Add token to request object for use in views
            request.jwt_token = token
        
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('userauths:sign-in'),
            reverse('userauths:sign-up'),
            reverse('userauths:sign-out'),
            reverse('base:index'),
        ]
        
        # Check if the current URL is public
        if request.path in public_urls:
            return None
            
        # Check if user is authenticated
        if not request.session.get('jwt_token'):
            messages.error(request, 'Please login to access this page.')
            return redirect('userauths:sign-in')
            
        return None 