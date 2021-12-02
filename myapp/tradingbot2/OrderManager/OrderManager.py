import pprint
import time
from binance.enums import *

class OrderManager:

    def __init__(self, client):
        print("order manager created")
        self.client = client
        self.ORDERS = {}
        self.FUTURES_ORDERS ={}
        self.IN_POSITION = []
        self.IN_HOLDING = []
        self.LAST_BUY_PRICE = {}

        self.leverage = 10
        self.testMode = False

        self.stop_loss = 0.0


    def create_market_order(self, symbol, amount):
        order = self.client.create_order(
            symbol=symbol.upper(),
            type='MARKET',
            side='BUY',
            newOrderRespType="RESULT",
            quoteOrderQty = str(amount)
        )
        return order

    def create_stoploss_order(self, symbol, amount, price):
        order = self.client.create_order(
            symbol=symbol.upper(),
            type='STOP_LOSS_LIMIT',
            side='SELL',
            timeInForce = "GTC",
            price = self._round(symbol, price),
            stopPrice = self._round(symbol, price*1.001),
            newOrderRespType="RESULT",
            quantity = str(amount)
        )
        return order
    
    def futures_create_market_order(self, symbol, qty):
        order = self.client.futures_create_order(
            symbol=symbol.upper(),
            type='MARKET',
            side='SELL',
            newOrderRespType="RESULT",
            quantity = str(qty)
        )
        pprint.pprint(order)
        return order


    def futures_create_stop_order(self, symbol, price):
        precision = self.get_baseAssetPrecision(symbol)
        order = self.client.futures_create_order(
            symbol=symbol.upper(),
            type='STOP_LIMIT',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price= float(price, precision),  #float The price at which you wish to buy/sell, float
            stopPrice = float(price*1.01, precision),
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity=0.001  # Number of coins you wish to buy / sell, float
        )
        return order
        
    def futures_create_stoploss_order(self, symbol, price, qty):
        order = self.client.futures_create_order(
            symbol=symbol.upper(),
            type='STOP',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price= round(price*0.99,2),
            stopPrice= price,  #price reach stopPrice will execute order at price
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity= str(qty)  # Number of coins you wish to buy / sell, string
        )
        pprint.pprint(order)
        return order


    def test_create_order(self, symbol, price, time):

        order = {
            "symbol": symbol.upper(),
            "orderId": 1,
            "price": price,
            "status": "FILLED",
            "type": "MARKET",
            "side": "BUY",
            "time": time
        }
        return order
    
    def test_create_stoploss_order(self, symbol, price, time):

        stoploss_order = {
            "symbol": symbol.upper(),
            "orderId": 1,
            "price": price,
            "status": "NEW",
            "type": "STOP_LOSS_LIMIT",
            "side": "SELL",
            "time": time
        }

        return stoploss_order

    def test_check_order_status(self, symbol, low_price):
        #if doesn't have any order yet
        try:
            if len(self.ORDERS[symbol]) == 0:
                return False
        except KeyError:
            return False

        order, stoploss_order = self.ORDERS[symbol][len(self.ORDERS[symbol]) - 1]

        ## handle status "NEW" of stpoloss_order
        ##manual check if order is filled
        if stoploss_order['status'] == "NEW" and low_price <= float(stoploss_order['price']):
            #stop loss met
            stoploss_order['status'] == "FILLED"
            self.IN_HOLDING.remove(symbol)

            return False # order not active anymore

        return True # order is active 


    def futures_set_leverage(self, symbol, leverage):
        self.client.futures_change_leverage(symbol=symbol.upper(), leverage=10)


    def futures_get_price(self, symbol):
        price = self.client.futures_symbol_ticker(symbol = symbol)['price']
        return float(price)

    def futures_get_all_orders(self):
        return self.client.futures_get_all_orders()
    
    def futures_get_open_orders(self):
        return self.client.futures_get_open_orders()

    def futures_get_balance(self):
        ##return usdt balance
        balances = self.client.futures_account_balance(asset="USDT")
        usdt = None

        for each in balances:
            if each['asset'] == "USDT":
                usdt = each
                break
        
        return float(usdt['balance'])

    def get_precision(self, symbol):
        #TODO: return precision of the base asset
        symbol_info = self.get_symbol_info(symbol)
        for i in symbol_info['filters']:
            if i['filterType'] == "PRICE_FILTER":
                price_precision = float(i['minPrice'])
        print(price_precision, len(str(price_precision)) - 2)
        return len(str(price_precision)) - 2

    def get_balance(self):
        ##return USDT balance
        #fetch details: {'asset': 'USDT', 'free': '11.73165240', 'locked': '0.00000000'}
        balance = self.client.get_asset_balance(asset='USDT')
        return float(balance["free"])

    def get_quantity(self, price, amount):
        return amount/price * self.leverage
    
    def _round(self, symbol, price):
        symbol_info = self.client.get_symbol_info(symbol)
        for i in symbol_info['filters']:
            if i['filterType'] == "PRICE_FILTER":
                minPrice = float(i['minPrice'])


        stopPrice = round(price, len(str(minPrice)) - 2)
        print("minPrice: ", minPrice)
        print("stopPrice: ", stopPrice)
        stopPrice += minPrice

        return round(stopPrice, len(str(minPrice)) - 2)
    
    
    def _add_to_memory(self, symbol, orders):
        try:
            orderId = str(len(self.ORDERS[symbol]) + 1)
        except KeyError:
            orderId = "1"
            self.ORDERS[symbol] = {}
        self.ORDERS[symbol][orderId] = orders
    
    def futures_add_to_memory(self, symbol, orders):
        try:
            orderId = str(len(self.FUTURES_ORDERS[symbol]) + 1)
        except KeyError:
            orderId = "1"
            self.FUTURES_ORDERS[symbol] = {}
        self.FUTURES_ORDERS[symbol][orderId] = orders
    

if __name__ == "__main__":
    from binance.enums import *
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")

    orderManager = OrderManager(client)

    pprint.pprint(orderManager.futures_get_balance())
    # orderManager.create_order("BNBUSDT", 11)
    # pprint.pprint(orderManager.ORDERS)


    # stoploss_price = 620.55
    # pprint.pprint(orderManager._stopPrice("BNBUSDT", 620.55*1.001))