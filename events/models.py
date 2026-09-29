from django.db import models
from django.conf import settings
from accounts.models import User


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('music', 'Music'),
        ('culture', 'Culture'),
        ('sports', 'Sports'),
        ('food', 'Food & Drinks'),
        ('networking', 'Networking'),
        ('arts', 'Arts'),
        ('film', 'Film'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    organiser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    location = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField()
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    permit_number = models.CharField(max_length=100, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    permit_verified = models.BooleanField(default=False)
    permit_tx_hash = models.CharField(max_length=100, blank=True)
    permit_block_number = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_started_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} by {self.organiser.username}'

    def is_approved(self):
        return self.status == 'approved'


class EventUpdate(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='updates')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Update for {self.event.title} at {self.created_at}'
    

class EventEvidence(models.Model):
    EVIDENCE_TYPE_CHOICES = [
        ('venue_confirmation', 'Venue Confirmation'),
        ('permit_document', 'Permit Document'),
        ('contact_log', 'Contact Log'),
        ('note', 'Admin Note'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='evidence')
    evidence_type = models.CharField(max_length=30, choices=EVIDENCE_TYPE_CHOICES)
    document = models.FileField(upload_to='evidence/', blank=True, null=True)
    document_hash = models.CharField(max_length=64, blank=True)
    note = models.TextField()
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.event.title} – {self.evidence_type} ({self.created_at:%Y-%m-%d})'