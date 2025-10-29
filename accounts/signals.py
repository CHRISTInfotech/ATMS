# accounts/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import redirect

@receiver(user_logged_in)
def role_based_redirect(sender, request, user, **kwargs):
    # You can check user role via custom fields or attributes
    if user.is_superuser:  # Admin check, assuming is_superuser is admin
        return redirect('accounts:admin_dashboard')
    elif hasattr(user, 'hod_profile'):  # If user has 'hod_profile' as a custom attribute
        return redirect('accounts:hod_dashboard')
    else:  # Default to staff or other roles
        return redirect('accounts:staff_dashboard')
