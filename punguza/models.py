from django.db import models


class Punguza(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    place = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='drinks/', blank=True, null=True)
    last_verified = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.name} — KSH {self.price}"

    def __str__(self):
        return self.name