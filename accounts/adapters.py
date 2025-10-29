# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import CustomUser
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Save the user and assign role from session if provided.
        """
        role = request.session.get('role')
        if role:
            user.role = role
        return super().save_user(request, user, form, commit)

    def is_open_for_signup(self, request):
        """
        Only allow signup/login if the email exists in CustomUser.
        Prevents creation of new users via normal signup.
        """
        email = request.session.get('account_email') or request.POST.get('login') or request.POST.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            return True
        return False  # Block unknown emails


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Called after Google authentication but before login.
        Only allow login if user already exists.
        """
        email = sociallogin.account.extra_data.get('email')
        if not email:
            # If Google didn't return email, block login
            sociallogin.state['process'] = 'login'
            sociallogin.user = None
            return

        try:
            # Try to find existing user
            user = CustomUser.objects.get(email=email)
            # Link the Google account to the existing user
            sociallogin.connect(request, user)
        except CustomUser.DoesNotExist:
            # Email not in CustomUser -> block login, do NOT create new user
            raise ImmediateHttpResponse(redirect('accounts:email_not_registered'))

