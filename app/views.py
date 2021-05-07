from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.views.generic import ListView
from .forms import OrderForm
from .models import Order, Profile, Transaction

# homepage with all orders
class HomeView(LoginRequiredMixin, ListView):
    queryset = Order.objects.all().order_by('-datetime')
    template_name = "app/homepage.html"
    context_object_name = "orders_list"


@login_required
def new_order_view(request):
    form = OrderForm(request.POST)
    if form.is_valid():
        form.save(commit=False)
        form.instance.user = request.user
        form.instance.profile = Profile.objects.get(user=request.user)

        # check if user's USD wallet can cover the order
        if form.instance.position == 'BUY' and (form.instance.price * form.instance.quantity) > form.instance.profile.USD_wallet:
            messages.warning(request, 'You cannot afford this Order!')
            return redirect("/new-order/")

        # check if user's BTC wallet can cover the order
        if form.instance.position == 'SELL' and form.instance.quantity > form.instance.profile.BTC_wallet:
            messages.warning(request, 'You cannot sell more BTCs than you have!')
            return redirect("/new-order/")

        # if user is submitting a BUY order and there is at least one SELL order with lower or equal price...
        if form.instance.position == 'BUY' and Order.objects.filter(position='SELL', price__lte=form.instance.price, status='open').count() > 0:
            print("Order matched!")
            # get the first order that matches the condition
            sell_order = Order.objects.filter(position='SELL', price__lte=form.instance.price, status='open').earliest('datetime')
            seller_profile = Profile.objects.get(_id=sell_order.profile._id)
            buyer_profile = Profile.objects.get(user=form.instance.user)
            desidered_btc = form.instance.quantity

            # if the quantity on sale is less or equal than the desired quantity
            if sell_order.quantity <= desidered_btc:

                buyer_profile.USD_wallet -= (float(sell_order.price) * float(sell_order.quantity))
                buyer_profile.BTC_wallet += float(sell_order.quantity)
                seller_profile.USD_wallet += (float(sell_order.price) * float(sell_order.quantity))
                seller_profile.BTC_wallet -= float(sell_order.quantity)
                # SELL order is done
                sell_order.status = 'closed'
                sell_order.save()
                # update BUY order detracting BTCs sold
                form.instance.quantity -= sell_order.quantity
                # create Transaction
                Transaction.objects.create(buyer=form.instance.user,
                                           seller=seller_profile.user,
                                           quantity=sell_order.quantity,
                                           price=sell_order.price)
                # calculate profit/loss for each part
                buyer_profile.profit -= (sell_order.price * sell_order.quantity)
                seller_profile.profit += (sell_order.price * sell_order.quantity)

                messages.success(request, 'Your Order has been created successfully and already involved transactions, please check your profile!')

            #  if the quantity on sale is greater than the desired quantity
            else:
                buyer_profile.USD_wallet -= (float(sell_order.price) * float(desidered_btc))
                buyer_profile.BTC_wallet += float(desidered_btc)
                seller_profile.USD_wallet += (float(sell_order.price) * float(desidered_btc))
                seller_profile.BTC_wallet -= float(desidered_btc)
                # BUY order is done
                form.instance.status = 'closed'
                # update SELL order detracting BTCs sold
                sell_order.quantity -= float(desidered_btc)
                sell_order.save()
                # create Transaction
                Transaction.objects.create(buyer=form.instance.user,
                                           seller=seller_profile.user,
                                           quantity=desidered_btc,
                                           price=sell_order.price)
                # calculate profit/loss for each party
                buyer_profile.profit -= (sell_order.price * desidered_btc)
                seller_profile.profit += (sell_order.price * desidered_btc)

                messages.success(request, 'Your Order has been created successfully and already involved transactions, please check your profile!')

            # if the order reach zero BTC quantity it is done
            if form.instance.quantity == 0.0:
                form.instance.status = 'closed'

            seller_profile.save()
            buyer_profile.save()
            form.save()

        elif form.instance.position == 'SELL' and Order.objects.filter(position='BUY', price__gte=form.instance.price, status='open').count() > 0:
            print("Order matched!")
            buy_order = Order.objects.filter(position='BUY', price__gte=form.instance.price, status='open').earliest('datetime')
            seller_profile = Profile.objects.get(user=form.instance.user)
            buyer_profile = Profile.objects.get(_id=buy_order.profile._id)
            btc_on_sale = form.instance.quantity

            if buy_order.quantity <= btc_on_sale:
                buyer_profile.USD_wallet -= (float(form.instance.price) * float(buy_order.quantity))
                buyer_profile.BTC_wallet += float(buy_order.quantity)
                seller_profile.USD_wallet += (float(form.instance.price) * float(buy_order.quantity))
                seller_profile.BTC_wallet -= (float(buy_order.quantity))
                buy_order.status = 'closed'
                buy_order.save()
                form.instance.quantity -= buy_order.quantity
                Transaction.objects.create(buyer=buyer_profile.user,
                                           seller=form.instance.user,
                                           quantity=buy_order.quantity,
                                           price=form.instance.price)
                buyer_profile.profit -= form.instance.price * buy_order.quantity
                seller_profile.profit += form.instance.price * buy_order.quantity

                messages.success(request, 'Your Order has been created successfully and already involved transactions, please check your profile!')

            else:
                buyer_profile.USD_wallet -= (float(form.instance.price) * float(btc_on_sale))
                buyer_profile.BTC_wallet += float(btc_on_sale)
                seller_profile.USD_wallet += (float(form.instance.price) * float(btc_on_sale))
                seller_profile.BTC_wallet -= (float(btc_on_sale))
                form.instance.status = 'closed'
                buy_order.quantity -= float(btc_on_sale)
                buy_order.save()
                Transaction.objects.create(buyer=buyer_profile.user,
                                           seller=form.instance.user,
                                           quantity=buy_order.quantity,
                                           price=form.instance.price)
                buyer_profile.profit -= form.instance.price * btc_on_sale
                seller_profile.profit += form.instance.price * btc_on_sale

                messages.success(request, 'Your Order has been created successfully and already involved transactions, please check your profile!')

            if form.instance.quantity == 0.0:
                form.instance.status = 'closed'

            seller_profile.save()
            buyer_profile.save()
            form.save()

        else:
            form.save()
            messages.success(request, 'Your Order has been created successfully!')

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
def user_profile_json_view(request):
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





