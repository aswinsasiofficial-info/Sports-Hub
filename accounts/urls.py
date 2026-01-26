from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('venues/', views.owner_venues, name='owner_venues'),
    path('profile/', views.profile, name='profile'),
    path('download-invoice/<int:booking_id>/', views.download_invoice, name='download_invoice'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('change-password/', views.change_password, name='change_password'),
]