from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount

@receiver(user_signed_up)
def set_google_signup_flag(request, user, **kwargs):
    # Check if the signup was via Google
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        request.session['google_signup'] = True 