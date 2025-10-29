# auth_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Add your app's URL patterns here
    # Example:
    path('home/', views.home, name='home'),
        # Example URL patterns
    path('login/', views.login_view, name='login'),
    # path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
]
