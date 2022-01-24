from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from .forms import OrderForm
from .models import Order, Profile, Transaction
from .utils import BitcoinBot
from .orderbook import Orderbook

# homepage with all orders
def homepage(request):

    price = 0  # BitcoinBot().get_price()
    var_24h = 0  # BitcoinBot().get_var()
    orders = Order.objects.exclude(status="closed").order_by("-datetime")
    context = {"orders": orders, "price": price, "var_24h": var_24h}

    return render(request, "app/homepage.html", context)


@login_required
def new_order_view(request):
    form = OrderForm(request.POST)
    if form.is_valid():
        form.save(commit=False)
        form.instance.user = request.user
        form.instance.profile = Profile.objects.get(user=request.user)

        # avoid orders with negative prices or quantity
        if form.instance.price < 0 or form.instance.quantity < 0:
            messages.warning(request, "You cannot place an order with negative values!")
            return redirect("/new-order/")

        # check if user's USD wallet can cover the order
        if (
            form.instance.position == "BUY"
            and (form.instance.price * form.instance.quantity)
            > form.instance.profile.USD_wallet
        ):
            messages.warning(request, "You cannot afford this Order!")
            return redirect("/new-order/")

        # check if user's BTC wallet can cover the order
        if (
            form.instance.position == "SELL"
            and form.instance.quantity > form.instance.profile.BTC_wallet
        ):
            messages.warning(request, "You cannot sell more BTCs than you have!")
            return redirect("/new-order/")

        form.save()
        messages.success(
            request,
            "Your Order has been created successfully, please check your profile for involved transactions!",
        )

        orderbook = Orderbook()
        new_order = orderbook.new_order

        # Market Orders
        if new_order.market_price == True:

            # Market buy order
            if new_order.position == "BUY" and orderbook.open_sell_orders.count() > 0:
                orderbook.market_buy_order_matching()

            elif new_order.position == "SELL" and orderbook.open_buy_orders.count() > 0:
                orderbook.market_sell_order_matching()

        # Limit Orders
        else:
            if new_order.position == "BUY" and orderbook.open_sell_orders.count() > 0:
                orderbook.limit_buy_order_matching()
            elif new_order.position == "SELL" and orderbook.open_buy_orders.count() > 0:
                orderbook.limit_sell_order_matching()

        return redirect("/")

    context = {"form": form}
    return render(request, "app/new_order.html", context)


# a view that returns all active orders
def open_orders_json_view(request):
    response = []
    orders = Order.objects.filter(status="open").order_by("-datetime")
    for order in orders:
        response.append(
            {
                "user": order.profile.user.username,
                "position": order.position,
                "quantity": order.quantity,
                "price": order.price,
                "datetime": order.datetime,
            }
        )
    return JsonResponse(response, safe=False)


# a view that returns profit/losses for each profile
@staff_member_required
def profit_and_losses_view(request):
    response = []
    profiles = Profile.objects.all()
    for profile in profiles:
        response.append(
            {
                "user": profile.user.username,
                "BTC_wallet": profile.BTC_wallet,
                "USD_wallet": profile.USD_wallet,
                "profit/losses": profile.profit,
            }
        )
    return JsonResponse(response, safe=False)


# a view that returns all transactions related to a user
def user_transactions_json_view(request):
    response = []
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    )
    for transaction in transactions:
        response.append(
            {
                "buyer": transaction.buyer.username,
                "seller": transaction.seller.username,
                "quantity": transaction.quantity,
                "price": transaction.price,
                "datetime": transaction.datetime,
            }
        )

    return JsonResponse(response, safe=False)


# profile view with user current balance and history of orders/transactions
def user_profile_view(request, id):
    user = get_object_or_404(User, id=id)
    profile = Profile.objects.get(user=user)
    orders = Order.objects.filter(profile=profile).order_by("-datetime")
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by("-datetime")

    context = {
        "user": user,
        "profile": profile,
        "orders": orders,
        "transactions": transactions,
    }

    return render(request, "app/profile.html", context)
