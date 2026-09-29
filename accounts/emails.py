from django.core.mail import send_mail
from django.conf import settings


def send_verification_approved_email(user):
    send_mail(
        subject='Your Evently Organiser Account Has Been Verified',
        message=f'Hi {user.username},\n\nYour organiser account has been approved. You can now create and publish events on Evently.\n\nThe Evently Team',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_verification_rejected_email(user):
    send_mail(
        subject='Evently Organiser Verification Update',
        message=f'Hi {user.username},\n\nUnfortunately your verification document was not approved. Please log in and resubmit with a valid official document.\n\nThe Evently Team',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_event_approved_email(event):
    send_mail(
        subject=f'Your Event "{event.title}" Has Been Approved',
        message=f'Hi {event.organiser.username},\n\nYour event "{event.title}" has been approved and is now live on Evently.\n\nThe Evently Team',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[event.organiser.email],
        fail_silently=False,
    )


def send_event_rejected_email(event):
    send_mail(
        subject=f'Your Event "{event.title}" Was Not Approved',
        message=f'Hi {event.organiser.username},\n\nYour event "{event.title}" was not approved. Please log in to review the admin notes and resubmit.\n\nThe Evently Team',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[event.organiser.email],
        fail_silently=False,
    )


def send_flag_notification_email(flag):
    from accounts.models import User
    admins = User.objects.filter(is_staff=True)
    admin_emails = [admin.email for admin in admins]
    if admin_emails:
        send_mail(
            subject=f'New Flag Submitted on Evently',
            message=f'A flag has been submitted on the event "{flag.event.title}" by {flag.user.username}.\n\nReason: {flag.reason}\n\nPlease review it at /flagging/admin/flags/\n\nThe Evently System',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )

def send_welcome_email(user):
    role = user.get_role_display()
    send_mail(
        subject='Welcome to Evently!',
        message=f'Hi {user.username},\n\nWelcome to Evently! Your account has been successfully created as a {role}.\n\nYou can now log in and explore personalised events in Nairobi.\n\nThe Evently Team',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_verification_submitted_email(user):
    send_mail(
        subject='Verification Document Received - Evently',
        message=f'Hi {user.username},\n\nWe have received your verification document. Our admin team will review it shortly and notify you of the outcome.\n\nThe Evently Team',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_verification_submitted_admin_email(user):
    from accounts.models import User as UserModel
    admins = UserModel.objects.filter(is_staff=True)
    admin_emails = [admin.email for admin in admins]
    if admin_emails:
        send_mail(
            subject='New Organiser Verification Document Submitted',
            message=f'Organiser {user.username} ({user.email}) has submitted a verification document and is awaiting review.\n\nLog in to the admin panel to review it.\n\nThe Evently System',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )


def send_event_submitted_admin_email(event):
    from accounts.models import User as UserModel
    admins = UserModel.objects.filter(is_staff=True)
    admin_emails = [admin.email for admin in admins]
    if admin_emails:
        send_mail(
            subject=f'New Event Submitted for Review: "{event.title}"',
            message=f'Organiser {event.organiser.username} has submitted a new event titled "{event.title}" scheduled for {event.date} in {event.location}.\n\nLog in to review it at /events/admin/pending/\n\nThe Evently System',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )