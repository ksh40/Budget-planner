from django.urls import path
from . import views
urlpatterns =[
    path('', views.food_home_view, name='food_home'),
]