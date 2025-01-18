from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('start_debugging/', views.start_debugging, name='start_debugging'),
    path('step_forward/', views.step_forward, name='step_forward'),  # For stepping to the next line
    path('stop_debugging/', views.stop_debugging, name='stop_debugging'),
]