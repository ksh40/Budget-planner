from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile


class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'username', 'role', 'verification_status', 'is_verified', 'is_staff']
    list_filter = ('role', 'is_verified', 'verification_status')
    readonly_fields = ('verification_document_hash',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'username', 'role')}),
        ('Verification', {'fields': ('verification_document','verification_document_hash', 'is_verified', 'verification_status', 'verification_notes')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'username', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ['email', 'username']
    actions = ['approve_organisers', 'reject_organisers']

    def approve_organisers(self, request, queryset):
        from .emails import send_verification_approved_email
        for user in queryset.filter(role='organiser'):
            user.is_verified = True
            user.verification_status = 'approved'
            user.save()
            send_verification_approved_email(user)
        self.message_user(request, 'Selected organisers have been approved and notified.')
    approve_organisers.short_description = 'Approve selected organisers'

    def reject_organisers(self, request, queryset):
        from .emails import send_verification_rejected_email
        for user in queryset.filter(role='organiser'):
            user.is_verified = False
            user.verification_status = 'rejected'
            user.save()
            send_verification_rejected_email(user)
        self.message_user(request, 'Selected organisers have been rejected and notified.')
    reject_organisers.short_description = 'Reject selected organisers'


admin.site.register(User, UserAdmin)
admin.site.register(Profile)