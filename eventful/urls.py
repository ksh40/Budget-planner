from django.urls import path
from . import views

urlpatterns = [
    path('', views.eventful_home_view, name='eventful_home'),
]