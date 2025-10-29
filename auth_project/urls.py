"""
URL configuration for auth_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# auth_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView  # Import Django's built-in LoginView
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Include your accounts app URLs
    path('', LoginView.as_view(template_name='accounts/login.html'), name='login'),  # Redirect root to the login page with custom template
    path('dashboard/', views.dashboard, name='dashboard'),
    path('app/', include('auth_app.urls')),  # Include other app URLs
    path('auth/', include('auth_app.urls')),  # Include other app URLs
    path('accounts/', include('allauth.urls')),  # Include Django Allauth's URLs for social login (including Google login)
]

