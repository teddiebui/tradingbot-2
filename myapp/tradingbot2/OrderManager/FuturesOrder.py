class FuturesOrder:
    def __init__(self, client, symbol, futures = False):
        pass
        self.client = client
        self.symbol = symbol.upper()
        self.futures = futures
        self.LEVERAGE = 10
        self.FUTURES_TRADE_SIZE = 0.01
        self.ORDER_LOG = []
        self.stop_loss = 0.02
        self.balance = 0
        self.futures_balance = 0
        self.precision = 0
        self.test = False
        self.trailing_stop_price = 0
        self.futures_trailing_stop_price = 0

    def futures_create_order_market(self, price):
        #TODO: create order stoploss
        self.futures_set_leverage()

        # quantity = self.futures_get_quantity(self.futures_get_balance()*self.FUTURES_TRADE_SIZE, price)
        quantity = self.futures_get_quantity(self.futures_get_balance()*self.FUTURES_TRADE_SIZE, price)

        print("quantity: ", quantity)
        print("total: ", quantity * price)

        # return self

        order = self.client.futures_create_order(
            symbol=self.symbol,
            type='MARKET',
            side='BUY',
            newOrderRespType="RESULT",
            quantity = str(quantity)
        )

        self.futures_trailing_stop_price = float(order["avgPrice"])
        self.ORDER_LOG.append(order)
        return self
    
    def futures_create_order_stoploss(self):
        #TODO: create order stoploss

        origOrder = self.ORDER_LOG[-1]

        price = round(float(origOrder["avgPrice"]) * (1 - self.stop_loss), self.get_price_precision())
        stop_price = round(price*1.005, self.get_price_precision())
        quantity = float(origOrder["origQty"])

        order = self.client.futures_create_order(
            symbol=self.symbol,
            type='STOP',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price= price,
            stopPrice= stop_price,  #price reach stopPrice will execute order at price
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            quantity= str(quantity)  # Number of coins you wish to buy / sell, string
        )
        self.ORDER_LOG.append(order)
        return self

    def futures_update_order(self, price):
        #met stop loss
        if self.is_active() and price <= float(self.ORDER_LOG[-1]['price']):
            updateOrder = self.client.futures_get_order(symbol = self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
            if updateOrder['status'] == "FILLED":
                self.ORDER_LOG[-1] = updateOrder

        
    
    def futures_trailing_stop(self, price):
        print("self.futures_trailing_stop_price", self.futures_trailing_stop_price)
        if self.is_active() and price > self.futures_trailing_stop_price:

            #move price up
            #step 1: cancel order
            if self.futures_cancel_order():
                print("futures order of {} has ben canceld".format(self.symbol))


                #step2: create new stoploss
                origOrder = self.ORDER_LOG[-1]
                price = round(price * (1-self.stop_loss), self.get_price_precision())
                stop_price = round(price*1.005, self.get_price_precision())
                quantity = origOrder['origQty']

                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    type='STOP',
                    timeInForce='GTC',  # Can be changed - see link to API doc below
                    price= price,
                    stopPrice= stop_price,  #price reach stopPrice will execute order at price
                    side='SELL',  # Direction ('BUY' / 'SELL'), string
                    quantity= str(quantity)  # Number of coins you wish to buy / sell, string

                )

                self.futures_trailing_stop_price = price
                self.ORDER_LOG.append(order)
            else:
                print("futures order of {} has NOT been canceld".format(self.symbol))
    
    def futures_get_quantity(self, amount, price):
        return round(amount/price * self.LEVERAGE, self.get_quantity_precision())
    
    def futures_cancel_order(self):
        self.ORDER_LOG[-1] = self.client.futures_cancel_order(symbol=self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
        return self.is_canceled()
    
    def futures_set_leverage(self, leverage = 10):
        self.client.futures_change_leverage(symbol=self.symbol, leverage=leverage)