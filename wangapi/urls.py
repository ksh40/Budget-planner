from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.WangapiLoginView.as_view(), name='wangapi_login'),
    path('register/', views.register_view, name='wangapi_register'),
    path('logout/', LogoutView.as_view(next_page='homeplan'), name='wangapi_logout'),
    path('profile/', views.profile_view, name='wangapi_profile'),
    path('toggle/', views.toggle_view, name='wangapi_toggle'),
    path('delete/', views.delete_account_view, name='wangapi_delete'),
    path('analytics/', views.analytics_view, name='wangapi_analytics'),
]
