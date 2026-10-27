from django.db import models
from django.core.validators import MaxValueValidator
class Students(models.Model):
   
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    og_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    discount = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(100)])
    discount_note = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=150)
    area = models.CharField(max_length=100, default="Nairobi")
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    image = models.ImageField(upload_to='students/', blank=True, null=True)
    last_verified = models.DateField(auto_now=True)

    @property
    def savings(self):
        if self.og_price and self.og_price > self.price:
            return self.og_price - self.price
        return None

    @property
    def percent_off(self):
        if self.savings:
            return round(self.savings / self.og_price * 100)
        return self.discount

    def __str__(self):
        return f"{self.name} — KSH {self.price}"
        
