from django.contrib import admin
from .models import Profile, Order, Transaction

admin.site.register(Profile)
admin.site.register(Order)
admin.site.register(Transaction)
# Register your models here.
