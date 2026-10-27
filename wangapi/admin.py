from django.contrib import admin
from django.db.models import Count
from django.utils.crypto import get_random_string

from .models import Bookmark, WangapiAccount
from .utils import PLACEHOLDER_SUFFIX


@admin.register(WangapiAccount)
class WangapiAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'date_joined', 'last_login', 'is_active', 'saved_count')
    search_fields = ('username',)
    ordering = ('-date_joined',)
    fields = ('username', 'date_joined', 'last_login', 'is_active')
    readonly_fields = ('username', 'date_joined', 'last_login')
    actions = ['reset_password']

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(email__endswith=PLACEHOLDER_SUFFIX, is_staff=False)
            .annotate(_saves=Count('wangapi_bookmarks'))
        )

    @admin.display(description='Saved posts', ordering='_saves')
    def saved_count(self, obj):
        return obj._saves

    @admin.action(description='Reset password (shows a temporary one)')
    def reset_password(self, request, queryset):
        for user in queryset:
            temporary = get_random_string(10)
            user.set_password(temporary)
            user.save(update_fields=['password'])
            self.message_user(request, f'{user.username}: {temporary}')

    def has_add_permission(self, request):
        return False


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'object_id', 'created')
    list_filter = ('kind',)
    search_fields = ('user__username',)
