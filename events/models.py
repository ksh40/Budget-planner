from django.db import models
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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