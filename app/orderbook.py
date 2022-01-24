from .models import Order, Transaction


class Orderbook:

    # total orderbook
    def __init__(self):
        self.new_order = Order.objects.latest("datetime")
        self.open_buy_orders = (
            Order.objects.filter(position="BUY", status="open")
            .exclude(profile=self.new_order.profile)
            .order_by("-price")
        )
        self.open_sell_orders = (
            Order.objects.filter(position="SELL", status="open")
            .exclude(profile=self.new_order.profile)
            .order_by("price")
        )

    def limit_buy_order_matching(self):

        for open_sell_order in self.buy_orderopen_sell_orders:
            if open_sell_order.price <= self.new_order.price:
                self.buy_order(self.new_order, open_sell_order)

    def limit_sell_order_matching(self):

        for open_buy_order in self.open_buy_orders:
            if open_buy_order.price >= self.new_order.price:
                self.sell_order(self.new_order, open_buy_order)

    def market_buy_order_matching(self):

        for open_sell_order in self.open_sell_orders:
            self.buy_order(self.new_order, open_sell_order)

    def market_sell_order_matching(self):

        for open_buy_order in self.open_buy_orders:
            self.sell_order(self.new_order, open_buy_order)

    def buy_order(self, new_order, open_sell_order):

        seller_profile = open_sell_order.profile
        buyer_profile = new_order.profile

        # if the quantity on sale is less or equal than the desired quantity
        if open_sell_order.quantity <= new_order.quantity:
            buyer_profile.USD_wallet -= open_sell_order.price * open_sell_order.quantity
            buyer_profile.BTC_wallet += open_sell_order.quantity
            seller_profile.USD_wallet += (
                open_sell_order.price * open_sell_order.quantity
            )
            seller_profile.BTC_wallet -= open_sell_order.quantity

            # update current order detracting BTC already sold
            new_order.quantity -= open_sell_order.quantity
            if new_order.quantity == 0.0:
                new_order.status = "closed"

            Transaction.objects.create(
                buyer=buyer_profile.user,
                seller=seller_profile.user,
                quantity=open_sell_order.quantity,
                price=open_sell_order.price,
            )

            buyer_profile.profit -= open_sell_order.price * open_sell_order.quantity
            seller_profile.profit += open_sell_order.price * open_sell_order.quantity

            # SELL order is done
            open_sell_order.status = "closed"
            open_sell_order.quantity = 0.0

        else:
            buyer_profile.USD_wallet -= open_sell_order.price * new_order.quantity
            buyer_profile.BTC_wallet += new_order.quantity
            seller_profile.USD_wallet += open_sell_order.price * new_order.quantity
            seller_profile.BTC_wallet -= new_order.quantity

            # update SELL order detracting BTCs already bought
            open_sell_order.quantity -= new_order.quantity

            Transaction.objects.create(
                buyer=new_order.profile.user,
                seller=seller_profile.user,
                quantity=new_order.quantity,
                price=open_sell_order.price,
            )

            buyer_profile.profit -= open_sell_order.price * new_order.quantity
            seller_profile.profit += open_sell_order.price * new_order.quantity

            # current order is done
            new_order.status = "closed"
            new_order.quantity = 0.0

        seller_profile.save()
        buyer_profile.save()
        new_order.save()
        open_sell_order.save()

    def sell_order(self, new_order, open_buy_order):

        buyer_profile = open_buy_order.profile
        seller_profile = new_order.profile

        if open_buy_order.quantity <= new_order.quantity:
            buyer_profile.USD_wallet -= open_buy_order.price * open_buy_order.quantity
            buyer_profile.BTC_wallet += open_buy_order.quantity
            seller_profile.USD_wallet += open_buy_order.price * open_buy_order.quantity
            seller_profile.BTC_wallet -= open_buy_order.quantity

            # update current order detracting BTCs already bought
            new_order.quantity -= open_buy_order.quantity
            if new_order.quantity == 0.0:
                new_order.status = "closed"

            Transaction.objects.create(
                buyer=buyer_profile.user,
                seller=seller_profile.user,
                quantity=open_buy_order.quantity,
                price=open_buy_order.price,
            )

            buyer_profile.profit -= open_buy_order.price * open_buy_order.quantity
            seller_profile.profit += open_buy_order.price * open_buy_order.quantity

            # BUY order is done
            open_buy_order.status = "closed"
            open_buy_order.quantity = 0.0

        else:
            buyer_profile.USD_wallet -= open_buy_order.price * new_order.quantity
            buyer_profile.BTC_wallet += new_order.quantity
            seller_profile.USD_wallet += open_buy_order.price * new_order.quantity
            seller_profile.BTC_wallet -= new_order.quantity

            # update BUY order detracting BTCs already sold
            open_buy_order.quantity -= new_order.quantity

            Transaction.objects.create(
                buyer=buyer_profile.user,
                seller=seller_profile.user,
                quantity=new_order.quantity,
                price=open_buy_order.price,
            )

            buyer_profile.profit -= new_order.price * new_order.quantity
            seller_profile.profit += new_order.price * new_order.quantity

            # current order is done
            new_order.status = "closed"
            new_order.quantity = 0.0

        seller_profile.save()
        buyer_profile.save()
        open_buy_order.save()
        new_order.save()
