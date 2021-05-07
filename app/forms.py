from django.forms import ModelForm
from .models import Order, Profile

# form to create a new order
class OrderForm(ModelForm):

    class Meta:
        model = Order
        fields = ['position', 'quantity', 'price']


