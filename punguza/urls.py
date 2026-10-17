from django.urls import path
from . import views

urlpatterns = [
    path('', views.punguza_home_view, name='punguza_home'),
]