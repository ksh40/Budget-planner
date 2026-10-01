from django.db import models

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('restaurants', 'Restaurants'),
        ('snack', 'Snack'),
        ('drink', 'Drink'),
    ]

    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    place = models.CharField(max_length=150)
    area = models.CharField(max_length=100)
    image = models.ImageField(upload_to='food_items/', blank=True, null=True)
    last_verified = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.name} — KSH {self.price}"


class Bundle(models.Model):
    title = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    items = models.ManyToManyField(Item, blank=True, related_name='bundles')
    image = models.ImageField(upload_to='food_bundles/', blank=True, null=True)
    last_verified = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.title} — KSH {self.price}"
