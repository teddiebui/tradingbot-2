import pprint

from binance.enums import *

class OrderManager:

    def __init__(self, client):
        print("order manager created")
        self.client = client
        self.ORDERS = {}
        self.FUTURES_ORDERS ={}

        self.leverage = 10

    
    
    def futures_create_order(self, symbol, amount):
        #amount in USDT
        #amount do not excess account's balance
        if amount >= self.futures_get_balance():
            print("amount excess balance in USDT")
        price = self.futures_get_price(symbol)
        quantity = self.get_quantity(price, amount)

        #set leverage
        self.futures_set_leverage(self.leverage)

        #create order_id
        order_id = len(self.FUTURES_ORDERS) + 1
        self.FUTURES_ORDERS[order_id] = []

        #create order
        order = self.futures_new_order_market(self, symbol)
        #create stop loss order
        stop_loss_order = self.futures_create_sl_order(symbol)

        self.FUTURES_ORDERS[order_id] = [order, stop_loss_order]


    def futures_set_leverage(self, symbol, leverage):
        self.client.futures_change_leverage(symbol=symbol.upper(), leverage=10)

    def futures_new_order_limit(self, symbol, price):
        order = self.client.futures_create_order(
            symbol=symbol.upper(),
            type='LIMIT',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price= price,  #float The price at which you wish to buy/sell, float
            side='BUY',  # Direction ('BUY' / 'SELL'), string
            quantity=0.001  # Number of coins you wish to buy / sell, float
        )

        pprint.pprint(order)
        return order

    def futures_new_order_market(self, symbol, qty):
        order = self.client.futures_create_order(
            symbol=symbol.upper(),
            type='MARKET',
            side='SELL',
            newOrderRespType="RESULT",
            quantity = str(qty)
        )

        # {'avgPrice': '0.00000',
        # 'clientOrderId': '2MKgqOn43oteMtiI1kgU13',
        # 'closePosition': False,
        # 'cumQty': '0',
        # 'cumQuote': '0',
        # 'executedQty': '0',
        # 'orderId': 36146159972,
        # 'origQty': '0.01',
        # 'origType': 'MARKET',
        # 'positionSide': 'BOTH',
        # 'price': '0',
        # 'priceProtect': False,
        # 'reduceOnly': False,
        # 'side': 'BUY',
        # 'status': 'NEW', 'FILLED'
        # 'stopPrice': '0',
        # 'symbol': 'BNBUSDT',
        # 'timeInForce': 'GTC',
        # 'type': 'MARKET',
        # 'updateTime': 1637197686998,
        # 'workingType': 'CONTRACT_PRICE'}
        pprint.pprint(order)
        return order
    def futures_create_sl_order(self, symbol, price, qty):
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

    
    def futures_get_price(self, symbol):
        price = self.client.futures_symbol_ticker(symbol = symbol)['price']
        return float(price)

        
    def futures_create_tp_order(self):
        pass

    def futures_check_trailing_stop(self):
        for order_id, order in self.FUTURES_ORDERS:
            last_order = order[-1]

    def futures_close_position(self):
        pass
    
    def futures_cancel_order(self, order_id):
        pass
    
    def cancel_order(self, orderId):
        pass
    
    def check_order_status(self, orderId):
        pass
        
    def finish_order(self, orderId):
        pass
    
    def futures_get_all_orders(self):
        return self.client.futures_get_all_orders()
    
    def futures_get_open_orders(self):
        return self.client.futures_get_open_orders()

    def futures_get_balance(self):
        ##return usdt balance
        balances = self.client.futures_account_balance()
        usdt = None

        for each in balances:
            if each['asset'] == "USDT":
                usdt = each;
                break;

        
        return float(usdt['balance']);

    def get_quantity(self, price, amount):
        return amount/price * self.leverage
    
    def _f_add(self, order):
        order_id = len(self.FUTURES_ORDERS)
        self.FUTURES_ORDERS[order_id] = order
        print("added order to futures order list")

    def _f_close(self, order):
        order_id = len(self.FUTURES_ORDERS)
        del self.FUTURES_ORDERS[order_id]

    def _add(self, order):
        order_id = len(self.ORDERS)
        self.ORDERS[order_id] = order
    
    def _close(self,order):
        order_id = len(self.ORDERS)
        del self.ORDERS[order_id]