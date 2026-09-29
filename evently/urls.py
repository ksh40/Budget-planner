from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from core.views import home_view as evently_home_view
from plan.views import home_view as plan_home_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('events/', include('events.urls')),
    path('search/', include('search.urls')),
    path('feedback/', include('feedback.urls')),
    path('flagging/', include('flagging.urls')),
    path('analytics/', include('analytics.urls')),
    path('plan/', include('plan.urls')),
    path('food/', include('food.urls')),


    path('evently/', evently_home_view, name='home'),   
    path('', plan_home_view, name='plan_home'), 
] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)