from django.urls import path
from . import views
urlpatterns =[
    path('', views.activities_home_view, name='activities_home'),
]
