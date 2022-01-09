import pprint
import time
import os


if __name__ == "__main__":
    from Order import Order
else:
    from ..OrderManager.Order import Order
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
        self.futures_balance = 0
        self.balance = 0

        self.file = __file__
    
    def create_order(self, symbol, trade_size):

        #check if symbol have pending order
        if symbol in self.ORDERS.keys() and not self.ORDERS[symbol][-1].is_finished():
            print(symbol + " have current pending order")
            return None
        #check if balance is sufficient

        balance = self.get_balance()
        if trade_size > balance or balance <= 11:
            print(symbol + " balance is not sufficient: trade size {} - balance {}".format(trade_size, balance))
            return None
        
        #create orders
        order = Order(self.client, symbol)
        order.create_order_market(trade_size)
        order.create_order_stoploss()

        try:
            self.ORDERS[symbol].append(order)
        except KeyError:
            self.ORDERS[symbol] = [order]

        return order

    def update_order(self, symbol, price):
        if symbol not in self.ORDERS.keys():
            ## there is no active order, no need to update
            return False

        if self.ORDERS[symbol][-1].met_stop_loss(price):
            ## if orderr is active and has met stop loss..
            print("%s stop loss met" % symbol)
            self.order_to_file(self.ORDERS[symbol][-1])
            return False

        if self.ORDERS[symbol][-1].trailing_stop(price):
            ## if orderr is active and has trailing stop successfully..
            print("%s trailing stop" % symbol)
            return True

    
    def futures_create_order(self, symbol, price):
        #check if symbol have pending order
        if symbol in self.FUTURES_ORDERS.keys() and self.FUTURES_ORDERS[symbol][-1].is_active():
            return None

        #check if balance is sufficient
        futures_balance = self.futures_get_balance()
        if (futures_balance <= 110):
            print(symbol + " futures balance is not sufficient. Balance: " + futures_balance)
            return None

        #create futures orders
        order = Order(self.client, symbol, True)
        order.futures_create_order_market(price)
        order.futures_create_order_stoploss()

        try:
            self.FUTURES_ORDERS[symbol].append(order)
        except KeyError:
            self.FUTURES_ORDERS[symbol] = [order]

        return order

    def futures_update_order(self, symbol, price):
        if symbol not in self.FUTURES_ORDERS.keys():
             ## there is no active order, no need to update
            return False

        if self.FUTURES_ORDERS[symbol][-1].futures_met_stop_loss(price):
            print("%s stop loss met" % symbol)
            self.futures_order_to_file(self.FUTURES_ORDERS[symbol][-1])
            return False
        if self.FUTURES_ORDERS[symbol][-1].futures_trailing_stop(price):
            print("futures %s trailing stop" % symbol)
            return True

        print("===========")

        
                        

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

    def get_balance(self):
        ##return USDT balance
        #fetch details: {'asset': 'USDT', 'free': '11.73165240', 'locked': '0.00000000'}
        balance = self.client.get_asset_balance(asset='USDT')
        return float(balance["free"])
    
    def futures_get_balance(self):
        ##return USDT balance
        #fetch details: {'asset': 'USDT', 'free': '11.73165240', 'locked': '0.00000000'}
        self.client.FUTURES_API_VERSION = 'v2'
        balance = self.client.futures_account_balance(asset='USDT')

        for each in balance:
            if each['asset'] == "USDT":
                self.futures_balance = float(each['maxWithdrawAmount'])
                self.client.FUTURES_API_VERSION = 'v1'
                break 
                    
        return self.futures_balance

    def order_to_file(self, order):
        filename = self._create_file_name()
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, "a+", encoding ="utf-8") as f:
            f.write(str(order.ORDER_LOG)+"\n")

    def futures_order_to_file(self, order):
        filename = "../jsondata/orders/futures_order.txt"
        filename = os.path.normpath(os.path.join(os.path.dirname(self.file), filename))


        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, "a+", encoding ="utf-8") as f:
            f.write(str(order.ORDER_LOG)+"\n")
    

    def _create_file_name(self):
        filename = "../jsondata/orders/order.txt"
        filename = os.path.normpath(os.path.join(os.path.dirname(self.file), filename))
        return filename

if __name__ == "__main__":

    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")

    orderManager = OrderManager(client)

    pprint.pprint(orderManager.futures_get_balance())
    pprint.pprint(orderManager.get_balance())
    orderManager.create_order("BNBUSDT", 11)
    orderManager.create_order("BNBUSDT", 11)
    # pprint.pprint(orderManager.ORDERS)


    # stoploss_price = 620.55
    # pprint.pprint(orderManager._stopPrice("BNBUSDT", 620.55*1.001))