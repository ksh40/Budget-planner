from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.recipe_list, name="list"),
    path("apply/", views.apply, name="apply"),
    path("new/", views.recipe_create, name="create"),
    path("<int:pk>/edit/", views.recipe_edit, name="edit"),
    path("<int:pk>/delete/", views.recipe_delete, name="delete"),
    path("<int:pk>/report/", views.recipe_report, name="report"),
]
