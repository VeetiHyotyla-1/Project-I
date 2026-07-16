from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=1000)

class PaymentProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    encrypted_card = models.BinaryField(null=True, blank=True)

class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.IntegerField()