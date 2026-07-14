from django.contrib import admin
from .models import Account, PaymentProfile, Transaction

admin.site.register(Account)
admin.site.register(PaymentProfile)
admin.site.register(Transaction)