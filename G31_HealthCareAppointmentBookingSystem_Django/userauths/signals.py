from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
# from django.db.models.signals import post_save
# from django.conf import settings
# import requests
# from userauths.models import User

@receiver(user_signed_up)
def set_google_signup_flag(request, user, **kwargs):
    # Check if the signup was via Google
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        request.session['google_signup'] = True 

# @receiver(post_save, sender=User)
# def sync_user_to_flask(sender, instance, created, **kwargs):
#     if created:
#         flask_api_url = getattr(settings, 'FLASK_API_URL', 'http://localhost:5000/api')
#         # Only sync if _raw_password is set (from registration form)
#         raw_password = getattr(instance, '_raw_password', None)
#         if not raw_password:
#             return  # Cannot sync without raw password
#         # Ensure full_name is not empty
#         full_name = getattr(instance, 'full_name', None) or instance.get_full_name() or instance.username or instance.email
#         try:
#             requests.post(
#                 f"{flask_api_url}/register",  # No trailing slash
#                 json={
#                     "email": instance.email,
#                     "password": raw_password,
#                     "full_name": full_name
#                 },
#                 timeout=5
#             )
#         except Exception as e:
#             print(f"Failed to sync user to Flask: {e}") 