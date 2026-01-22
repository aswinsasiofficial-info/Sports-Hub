from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('venues/', views.venue_list, name='venue_list'),
    path('venue/<int:venue_id>/', views.venue_detail, name='venue_detail'),
    path('sport/<str:sport_name>/', views.sport_venues, name='sport_venues'),
]