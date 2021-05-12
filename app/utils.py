import requests

class BitcoinBot:

    def __init__(self):
        self.url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        self.params = {
            "start": "1",
            "limit": "1",
            "convert": "USD"
        }
        self.headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": "e2ca6eee-614c-41f5-8d7a-daffd353223c"
        }

    def get_price(self):
        r = requests.get(url=self.url, headers=self.headers, params=self.params).json()
        price = round(r["data"][0]["quote"]["USD"]["price"], 2)
        return price

    def get_var(self):
        r = requests.get(url=self.url, headers=self.headers, params=self.params).json()
        var = round(r["data"][0]["quote"]["USD"]["percent_change_24h"], 2)
        return var


