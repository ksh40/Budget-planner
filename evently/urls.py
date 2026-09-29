from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from core.views import home_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('events/', include('events.urls')),
    path('search/', include('search.urls')),
    path('feedback/', include('feedback.urls')),
    path('flagging/', include('flagging.urls')),
    path('analytics/', include('analytics.urls')),
    path('', home_view, name='home'),
] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)