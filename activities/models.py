from django.db import models

from django.db import models


class Activity(models.Model):
   
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    location = models.CharField(max_length=150)
    area = models.CharField(max_length=100, default="Nairobi")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='activities/', blank=True, null=True)
    last_verified = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.name} — KSH {self.price}"
