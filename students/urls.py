from django.urls import path
from . import views
urlpatterns =[
    path('', views.students_home_view, name='students_home'),
]
