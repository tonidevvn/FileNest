"""URLs for monitoring app."""
from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('logs/', views.log_monitoring, name='logs'),
]
