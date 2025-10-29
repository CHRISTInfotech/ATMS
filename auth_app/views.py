# auth_app/views.py

from django.shortcuts import render

def login_view(request):
    # Your login view logic
    return render(request, 'auth_app/login.html')

# def signup_view(request):
#     # Your signup view logic
#     return render(request, 'auth_app/signup.html')

def profile_view(request):
    # Your profile view logic
    return render(request, 'auth_app/profile.html')

def home(request):
    # Your home view logic
    return render(request, 'auth_app/home.html')  # Ensure you have this template
