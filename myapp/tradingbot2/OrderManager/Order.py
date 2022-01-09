class Order:
    def __init__(self, client, symbol, futures = False):
        pass
        self.client = client
        self.symbol = symbol.upper()
        self.futures = futures
        self.LEVERAGE = 10
        self.FUTURES_TRADE_SIZE = 0.01
        self.ORDER_LOG = []
        self.stop_loss = 0.035
        self.balance = 0
        self.futures_balance = 0
        self.price_precision = 0
        self.quantity_precision = 0
        self.test = False
        self.trailing_stop_price = 0
        self.futures_trailing_stop_price = 0
        self.futures_price_precision = 0
        self.futures_quantity_precision = 0
        if self.futures:
            self.futures_set_leverage()
         

    def create_order_market(self, trade_size):
        #TODO: create order market

        order = self.client.create_order(
            symbol=self.symbol,
            type='MARKET',
            side='BUY',
            newOrderRespType="RESULT",
            quoteOrderQty = str(trade_size) ## trade_size in USDT
        )

        avgBuyPrice = round( float(order['cummulativeQuoteQty'])/float(order['executedQty']),self.get_price_precision())

        self.trailing_stop_price = avgBuyPrice
        self.ORDER_LOG.append(order)
        return self

    def create_order_stoploss(self):
        #TODO: create order stoploss
        origOrder = self.ORDER_LOG[-1]

        avgBuyPrice = round( float(origOrder['cummulativeQuoteQty'])/float(origOrder['executedQty']),self.get_price_precision())
        price = round(float(avgBuyPrice * (1 - self.stop_loss)), self.get_price_precision())
        stop_price = round(price*1.005, self.get_price_precision())
        quantity = float(origOrder["origQty"])

        order = self.client.create_order(
            symbol=self.symbol,
            type='STOP_LOSS_LIMIT',
            side='SELL',
            timeInForce = "GTC",
            price = price,
            stopPrice = stop_price,
            newOrderRespType="RESULT",
            quantity = str(quantity)
        )
        
        self.ORDER_LOG.append(order)
        return self

    def met_stop_loss(self, price):
        #met stop loss
        if self.is_active() and price <= float(self.ORDER_LOG[-1]['stopPrice']):
            updateOrder = self.client.get_order(symbol = self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
            if updateOrder['status'] == "FILLED":
                self.ORDER_LOG[-1] = updateOrder
                return True
        return False

    def trailing_stop(self, price):
        if self.is_active() and price > self.trailing_stop_price:
            #move price up
            #step 1: cancel order
            if self.cancel_order():
                #step2: create new stoploss
                new_price = round(price * (1-self.stop_loss), self.get_price_precision())
                stop_price = round(new_price*1.005, self.get_price_precision())
                quantity = self.ORDER_LOG[0]['origQty']

                order = self.client.create_order(
                    symbol=self.symbol,
                    type='STOP_LOSS_LIMIT',
                    timeInForce='GTC',  # Can be changed - see link to API doc below
                    price= new_price,
                    stopPrice= stop_price,  #price reach stopPrice will execute order at price
                    newOrderRespType="RESULT",
                    side='SELL',  # Direction ('BUY' / 'SELL'), string
                    quantity= str(quantity)  # Number of coins you wish to buy / sell, string

                )

                self.trailing_stop_price = price
                self.ORDER_LOG.append(order)
                return True
            else:
                print("order of {} has NOT been canceld".format(self.symbol))
        return False

    def cancel_order(self):
        try:
            self.ORDER_LOG[-1] = self.client.cancel_order(symbol=self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
        except:
            self.ORDER_LOG[-1] = self.client.get_order(symbol=self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
        return self.is_canceled()


    def futures_create_order_market(self, price):
        #TODO: create order stoploss
        quantity = self.futures_get_quantity(self.futures_get_balance()*self.FUTURES_TRADE_SIZE, price)

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

        price = round(float(origOrder["avgPrice"]) * (1 - self.stop_loss), self.get_futures_price_precision())
        stop_price = round(price*1.005, self.get_futures_price_precision())
        quantity = float(origOrder["origQty"])


        order = self.client.futures_create_order(
            symbol=self.symbol,
            type='STOP',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price= price,
            stopPrice= stop_price,  #price reach stopPrice will execute order at price
            side='SELL',  # Direction ('BUY' / 'SELL'), string
            newOrderRespType="RESULT",
            quantity= str(quantity)  # Number of coins you wish to buy / sell, string
        )
        self.ORDER_LOG.append(order)
        return self
    
    

    def futures_met_stop_loss(self, price):
        #met stop loss
        if self.is_active() and price <= float(self.ORDER_LOG[-1]['stopPrice']):
            updateOrder = self.client.futures_get_order(symbol = self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
            if updateOrder['status'] == "FILLED":
                self.ORDER_LOG[-1] = updateOrder
                return True
        return False

        
    
    def futures_trailing_stop(self, price):
        if self.is_active() and price > self.futures_trailing_stop_price:

            print(price, self.futures_trailing_stop_price, price > self.futures_trailing_stop_price)

            #move price up
            #step 1: cancel order
            if self.futures_cancel_order():
                #step2: create new stoploss
                origOrder = self.ORDER_LOG[-1]
                new_price = round(price * (1-self.stop_loss), self.get_price_precision())
                stop_price = round(new_price*1.005, self.get_price_precision())
                quantity = origOrder['origQty']

                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    type='STOP',
                    timeInForce='GTC',  # Can be changed - see link to API doc below
                    price= new_price,
                    stopPrice= stop_price,  #price reach stopPrice will execute order at price
                    newOrderRespType="RESULT",
                    side='SELL',  # Direction ('BUY' / 'SELL'), string
                    quantity= str(quantity)  # Number of coins you wish to buy / sell, string

                )

                self.futures_trailing_stop_price = price
                self.ORDER_LOG.append(order)
                return True
            else:
                print("futures order of {} has NOT been canceld".format(self.symbol))
        return False
        

    def futures_get_quantity(self, amount, price):
        return round(amount/price * self.LEVERAGE, self.get_futures_quantity_precision())
    
    def futures_cancel_order(self):
        try:
            self.ORDER_LOG[-1] = self.client.futures_cancel_order(symbol=self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
        except:
            self.ORDER_LOG[-1] = self.client.futures_get_order(symbol=self.symbol, origClientOrderId=self.ORDER_LOG[-1]['clientOrderId'])
        return self.is_canceled()

    def futures_set_leverage(self, leverage = 10):
        self.client.futures_change_leverage(symbol=self.symbol, leverage=leverage)

    def get_balance(self):
        ##return USDT balance
        #fetch details: {'asset': 'USDT', 'free': '11.73165240', 'locked': '0.00000000'}
        balance = self.client.get_asset_balance(asset='USDT')
        self.balance = float(balance["free"])
        return self.balance
    
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

    def get_futures_price_precision(self):

        if self.futures_price_precision == 0:
            ex = self.client.futures_exchange_info()
            for symbol_info in ex['symbols']:
                if symbol_info['symbol'] == self.symbol:
                    #derive price precision

                    for i in symbol_info['filters']:

                        if i['filterType'] == "PRICE_FILTER":
                            string = i['tickSize'][2:]
                            self.futures_price_precision = 0
                            for index in range(len(string)):
                                if string[index] != "0":
                                    self.futures_price_precision = index + 1
                                    break
                            break

                    ##
                    break
        return self.futures_price_precision

    def get_futures_quantity_precision(self):

        if self.futures_quantity_precision == 0:
            ex = self.client.futures_exchange_info()
            for symbol_info in ex['symbols']:
                if symbol_info['symbol'] == self.symbol:
                    #derive price precision
                    for i in symbol_info['filters']:

                        if i['filterType'] == "LOT_SIZE":

                            string = i['stepSize'][2:]

                            self.futures_quantity_precision = 0
                            for index in range(len(string)):
                                if string[index] != "0":
                                    self.futures_quantity_precision = index + 1
                                    break
                            break
                    ##
                    break
        return self.futures_quantity_precision

    def get_price_precision(self):
        #TODO: return precision of the base asset
        if self.price_precision == 0:
            symbol_info = self.client.get_symbol_info(self.symbol)

            for i in symbol_info['filters']:

                if i['filterType'] == "PRICE_FILTER":
                    string = i['tickSize'][2:]
                    self.price_precision = 0
                    for index in range(len(string)):
                        if string[index] != "0":
                            self.price_precision = index + 1
                            break
                    break
            

        return self.price_precision
    
    def get_quantity_precision(self):
        if self.quantity_precision == 0:

            symbol_info = self.client.get_symbol_info(self.symbol)

            for i in symbol_info['filters']:

                if i['filterType'] == "LOT_SIZE":
                    string = i['stepSize'][2:]
                    self.quantity_precision = 0
                    for index in range(len(string)):
                        if string[index] != "0":
                            self.quantity_precision = index + 1
                            break
                    break
            

        return self.quantity_precision

    

    def is_opened(self):
        return len(self.ORDER_LOG) != 0

    def is_active(self):
        if self.is_opened():
            return self.ORDER_LOG[-1]['status'] == "NEW"
        return False

    def is_finished(self):
        if self.is_opened():
            return self.ORDER_LOG[-1]['status'] == "FILLED"
        return False
    
    def is_canceled(self):
        print("order " + self.ORDER_LOG[-1]['clientOrderId'] +"is cancelled: ", self.ORDER_LOG[-1]['status'] == "CANCELED")
        return self.ORDER_LOG[-1]['status'] == "CANCELED"

    

if __name__ == "__main__":
    import pprint
    
    from binance.enums import *
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    client = Client("XJ3u04cEmn0CDTUamYRxv7e2hvqGESKswk1RJSCouHfyPc93fQBd4wplAIhXDUs6",  "Q5D1KVNcfom68qvGrBtLek2CMacZx71NjLzBsLxTqsxPYdaptzmiw3t7t23cR9hg")

    # client.futures_get_all_orders()
    # order = Order(client, "BNBUSDT", futures=True)
    # order.FUTURES_TRADE_SIZE = 0.01
    
    # order.update_order(546)

    # order.futures_trailing_stop(555)
    order = Order(client, "BNBUSDT", futures=True)
    
    print("order.get_futures_price_precision()", order.get_futures_price_precision())
    print("order.get_futures_quantity_precision()", order.get_futures_quantity_precision())
    print("===")
    
    print("order.get_price_precision()", order.get_price_precision())
    print("order.get_quantity_precision()", order.get_quantity_precision())
    print("===")
    ex = client.futures_exchange_info()

    orders = client.get_order(symbol ="WTCUSDT", origClientOrderId="kD6IXjhQxQNyMGQUYaOrdo")
    pprint.pprint(orders)

    # pprint.pprint(order.futures_get_balance())
    # pprint.pprint(order.get_balance())

    
    # for each in ex['symbols']:
    #     if each['symbol'] == "DENTUSDT":
    #         pprint.pprint(each)
    # pprint.pprint(len(ex['symbols']))
    # pprint.pprint(ex['symbols'][0])

    # order.futures_create_order_market(0.00495)
    # order.futures_create_order_stoploss()

    
    # pprint.pprint(order.ORDER_LOG)
    # pprint.pprint(client.futures_get_all_orders())
    # pprint.pprint(client.get_all_orders())
    # pprint.pprint(client.futures_get_order(symbol = 'CRVUSDT', origClientOrderId = 'ios_b7QoNg3vZdJtxDZGkTUE'))



    # ##tét normal order
    # order = Order(client, "BNBUSDT")
    # order.create_order_market(12)
    # order.create_order_stoploss()

    # #Test futures order
    # order = Order(client, "BNBUSDT")
    # order.futures_create_order_market(540)
    # order.futures_create_order_stoploss()

    # pprint.pprint(order.ORDER_LOG)
    # print("=========")
    # order.futures_trailing_stop(545)
    
    # pprint.pprint(order.ORDER_LOG)
    # print("=========")
    # order.futures_trailing_stop(542)

    # pprint.pprint(order.ORDER_LOG)
    # print("=========")
    # order.futures_trailing_stop(547)
    
    # pprint.pprint(order.ORDER_LOG)
    # print("=========")


    ##