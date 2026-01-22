from django.urls import path
from . import views

urlpatterns = [
    path('success/', views.payment_success, name='payment_success'),
    path('webhook/', views.payment_webhook, name='payment_webhook'),
]