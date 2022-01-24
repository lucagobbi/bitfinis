from xml.dom import ValidationErr
from django.forms import ModelForm
from .models import Order, Profile
from django.core.exceptions import ValidationError

# form to create a new order
class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ["position", "quantity", "price", "market_price"]

        def clean(self):
            data = self.cleaned_data

            market_price = data.get("market_price")
            price = data.get("price")

            if market_price == True and price != 0:
                raise ValidationError(
                    "You cannot set market price setting your own price!"
                )
