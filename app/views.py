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

# homepage with all orders
def homepage(request):

    #price = BitcoinBot().get_price()
    #var_24h = BitcoinBot().get_var()
    orders = Order.objects.all().order_by('-datetime')
    profile = Profile.objects.get(user=request.user)
    context = {"orders": orders, "profile": profile,} #"price": price, "var_24h": var_24h}

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
            messages.warning(request, 'You cannot place an order with negative values!')
            return redirect("/new-order/")

        # check if user's USD wallet can cover the order
        if form.instance.position == 'BUY' and (form.instance.price * form.instance.quantity) > form.instance.profile.USD_wallet:
            messages.warning(request, 'You cannot afford this Order!')
            return redirect("/new-order/")

        # check if user's BTC wallet can cover the order
        if form.instance.position == 'SELL' and form.instance.quantity > form.instance.profile.BTC_wallet:
            messages.warning(request, 'You cannot sell more BTCs than you have!')
            return redirect("/new-order/")

        form.save()
        messages.success(request, 'Your Order has been created successfully, please check your profile for involved transactions!')

        new_order = Order.objects.latest('datetime')
        open_buy_orders = Order.objects.filter(position='BUY', status='open').exclude(profile=new_order.profile).order_by('-price')
        open_sell_orders = Order.objects.filter(position='SELL', status='open').exclude(profile=new_order.profile).order_by('price')

        # BUY order
        if new_order.position == 'BUY' and open_sell_orders.count() > 0:

            for open_sell_order in open_sell_orders:

                if open_sell_order.price <= new_order.price:
                    seller_profile = open_sell_order.profile
                    buyer_profile = new_order.profile

                    # if the quantity on sale is less or equal than the desired quantity
                    if open_sell_order.quantity <= new_order.quantity:
                        buyer_profile.USD_wallet -= (open_sell_order.price * open_sell_order.quantity)
                        buyer_profile.BTC_wallet += open_sell_order.quantity
                        seller_profile.USD_wallet += (open_sell_order.price * open_sell_order.quantity)
                        seller_profile.BTC_wallet -= open_sell_order.quantity

                        # update current order detracting BTC already sold
                        new_order.quantity -= open_sell_order.quantity
                        if new_order.quantity == 0.0:
                            new_order.status = 'closed'

                        Transaction.objects.create(buyer=buyer_profile.user,
                                                   seller=seller_profile.user,
                                                   quantity=open_sell_order.quantity,
                                                   price=open_sell_order.price)

                        buyer_profile.profit -= (open_sell_order.price * open_sell_order.quantity)
                        seller_profile.profit += (open_sell_order.price * open_sell_order.quantity)

                        # SELL order is done
                        open_sell_order.status = 'closed'
                        open_sell_order.quantity = 0.0

                    else:
                        buyer_profile.USD_wallet -= (open_sell_order.price * new_order.quantity)
                        buyer_profile.BTC_wallet += new_order.quantity
                        seller_profile.USD_wallet += (open_sell_order.price * new_order.quantity)
                        seller_profile.BTC_wallet -= new_order.quantity

                        # update SELL order detracting BTCs already bought
                        open_sell_order.quantity -= new_order.quantity

                        Transaction.objects.create(buyer=new_order.profile.user,
                                                   seller=seller_profile.user,
                                                   quantity=new_order.quantity,
                                                   price=open_sell_order.price)

                        buyer_profile.profit -= (open_sell_order.price * new_order.quantity)
                        seller_profile.profit += (open_sell_order.price * new_order.quantity)

                        new_order.status = 'closed'
                        new_order.quantity = 0.0


                    seller_profile.save()
                    buyer_profile.save()
                    new_order.save()
                    open_sell_order.save()


        # SELL order
        if new_order.position == 'SELL' and open_buy_orders.count() > 0:

            for open_buy_order in open_buy_orders:

                if open_buy_order.price >= new_order.price:
                    buyer_profile = open_buy_order.profile
                    seller_profile = new_order.profile

                    if open_buy_order.quantity <= new_order.quantity:
                        buyer_profile.USD_wallet -= (open_buy_order.price * open_buy_order.quantity)
                        buyer_profile.BTC_wallet += open_buy_order.quantity
                        seller_profile.USD_wallet += (open_buy_order.price * open_buy_order.quantity)
                        seller_profile.BTC_wallet -= open_buy_order.quantity

                        # update current order detracting BTCs already bought
                        new_order.quantity -= open_buy_order.quantity
                        if new_order.quantity == 0.0:
                            new_order.status = 'closed'

                        Transaction.objects.create(buyer=buyer_profile.user,
                                                   seller=seller_profile.user,
                                                   quantity=open_buy_order.quantity,
                                                   price=open_buy_order.price)

                        buyer_profile.profit -= (open_buy_order.price * open_buy_order.quantity)
                        seller_profile.profit += (open_buy_order.price * open_buy_order.quantity)

                        # BUY order is done
                        open_buy_order.status = 'closed'
                        open_buy_order.quantity = 0.0

                    else:
                        buyer_profile.USD_wallet -= (open_buy_order.price * new_order.quantity)
                        buyer_profile.BTC_wallet += new_order.quantity
                        seller_profile.USD_wallet += (open_buy_order.price * new_order.quantity)
                        seller_profile.BTC_wallet -= new_order.quantity

                        # update BUY order detracting BTCs already sold
                        open_buy_order.quantity -= new_order.quantity

                        Transaction.objects.create(buyer=buyer_profile.user,
                                                   seller=seller_profile.user,
                                                   quantity=new_order.quantity,
                                                   price=open_buy_order.price)

                        buyer_profile.profit -= (new_order.price * new_order.quantity)
                        seller_profile.profit += (new_order.price * new_order.quantity)

                        # current order is done
                        new_order.status = 'closed'
                        new_order.quantity = 0.0

                    seller_profile.save()
                    buyer_profile.save()
                    open_buy_order.save()
                    new_order.save()

        return redirect("/")

    context = {
        'form': form
    }
    return render(request, "app/new_order.html", context)

# a view that returns all active orders
def open_orders_json_view(request):
    response = []
    orders = Order.objects.filter(status='open').order_by('-datetime')
    for order in orders:
        response.append(
            {
                'user': order.profile.user.username,
                'position': order.position,
                'quantity': order.quantity,
                'price': order.price,
                'datetime': order.datetime
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
                'user': profile.user.username,
                'BTC_wallet': profile.BTC_wallet,
                'USD_wallet': profile.USD_wallet,
                'profit/losses': profile.profit
            }
        )
    return JsonResponse(response, safe=False)

# a view that returns all transactions related to a user
def user_transactions_json_view(request):
    response = []
    transactions = Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user))
    for transaction in transactions:
        response.append(
            {
                'buyer': transaction.buyer.username,
                'seller': transaction.seller.username,
                'quantity': transaction.quantity,
                'price': transaction.price,
                'datetime': transaction.datetime
            }
        )

    return JsonResponse(response, safe=False)

# profile view with user current balance and history of orders/transactions
def user_profile_view(request, id):
    user = get_object_or_404(User, id=id)
    profile = Profile.objects.get(user=user)
    orders = Order.objects.filter(profile=profile).order_by('-datetime')
    transactions = Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user)).order_by('-datetime')
    context = {"user": user, "profile": profile, "orders": orders, "transactions": transactions}

    return render(request, "app/profile.html", context)




