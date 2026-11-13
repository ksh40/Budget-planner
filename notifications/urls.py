from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("read/", views.mark_all_read, name="mark_all_read"),
    path("open/<int:pk>/", views.open_notification, name="open"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("delete-all/", views.delete_all, name="delete_all"),
]
