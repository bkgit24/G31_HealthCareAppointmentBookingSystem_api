from django.urls import path
from django.contrib.auth import views as auth_views

from userauths import views as userauths_views
from .views import SelectRoleView, role_based_redirect

app_name = "userauths"

urlpatterns = [
    path("sign-up/", userauths_views.register_view, name="sign-up"),
    path("sign-in/", userauths_views.login_view, name="sign-in"),
    path("sign-out/", userauths_views.logout_view, name="sign-out"),
    path("select-role/", SelectRoleView.as_view(), name="select-role"),
    path('role-redirect/', role_based_redirect, name='role-redirect'),
    
    
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='userauths/password_reset.html',
        email_template_name='userauths/password_reset_email.html',
        subject_template_name='userauths/password_reset_subject.txt',
        success_url='/auth/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='userauths/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='userauths/password_reset_confirm.html',
        success_url='/auth/password-reset-complete/'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='userauths/password_reset_complete.html'
    ), name='password_reset_complete'),
]