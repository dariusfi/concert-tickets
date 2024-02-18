from django.db import models


class Customer(models.Model):
    email = models.EmailField(max_length=254)
    allows_advertising = models.BooleanField(default=False)

    def __str__(self):
        return self.email