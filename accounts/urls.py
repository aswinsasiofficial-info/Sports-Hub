from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('profile/', views.profile, name='profile'),
]