from django.db import models
from django.contrib.auth.models import User
from djongo.models.fields import ObjectIdField
import random


class Profile(models.Model):

    _id = ObjectIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    BTC_wallet = models.FloatField(default=random.randint(1, 10))
    USD_wallet = models.FloatField(default=0)
    profit = models.FloatField(default=0)

class Order(models.Model):
    CHOICES = (('BUY', 'BUY'), ('SELL', 'SELL'))

    _id = ObjectIdField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    position = models.CharField(max_length=10, choices=CHOICES, default='BUY')
    status = models.Field(default='open')
    datetime = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    quantity = models.FloatField()


class Transaction(models.Model):

    _id = ObjectIdField()
    buyer = models.ForeignKey(User, related_name='buyer', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='seller', on_delete=models.CASCADE)
    quantity = models.FloatField()
    price = models.FloatField()
    datetime = models.DateTimeField(auto_now_add=True)

# Create your models here.
