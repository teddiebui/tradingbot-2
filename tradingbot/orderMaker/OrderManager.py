import pprint
import math
import datetime
import time
import json
import os

from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

from ..priceMaker import priceMaker as pm


class OrderMaker(pm.PriceMaker):

    def __init__(self, client, symbol, stake, take_profit, stop_loss, fee, discount, trailing_stop_mode = False):
        
        self.client = client
        self.symbol = symbol

        pm.PriceMaker.__init__(self, stake, take_profit, stop_loss, fee, discount, precision = self._get_decimal_precision(symbol))
        
        
        self.current_position = None

        self.open_orders = []
        self.orders = []
        
        #load temp pending orders if any
        self._load_open_orders()
        
        #flags
        self.is_in_position = False
        self.trailing_stop_mode = trailing_stop_mode
        #temp variable
        self.prev_price = 0 #for trailing stop uses

    def buy_with_stop_limit(self, current_price = 0):
        
        if self.is_in_position == False:
            
            order_market_buy = self.client.order_market_buy(
                        symbol= self.symbol.upper(),
                        quoteOrderQty= round(self.stake, self.precision))
                        
                        
            pprint.pprint(order_market_buy)
            buy_price, qty, vol = self._extract_filled_order(order_market_buy)
            stop_loss_price = self.get_stop_loss_price(buy_price)
            # print(buy_price, round((stop_loss_price*1.001), self.precision))
            
            order_limit_sell = self.client.create_order(
                symbol= self.symbol,
                side=SIDE_SELL,
                type='STOP_LOSS_LIMIT',
                timeInForce=TIME_IN_FORCE_GTC,
                price = stop_loss_price, 
                stopPrice = round((stop_loss_price*1.000), self.precision),
                quantity=qty,
                newOrderRespType = 'FULL')
                
            pprint.pprint(order_limit_sell)
            
            record = {
                'recordId' : order_market_buy['orderId'],
                'recordData': [order_market_buy, order_limit_sell]
            }
            
            self.orders.append(record)
            self.open_orders.append(record['recordData'])
            self.is_in_position = True
            self.prev_price = buy_price
            
            self._log_temp()
                    
    def buy_with_oco(self, current_price = 0.00):
        
        if self.is_in_position == False:
            self.is_in_position = True


            order_market_buy = self.client.order_market_buy(
                        symbol= self.symbol.upper(),
                        quoteOrderQty= round(self.stake, self.precision))
                        
            buy_price, quantity, volume = self._extract_filled_order(order_market_buy)

            # self.orders[str(len(self.orders) + 1)] = [order_market_buy]

            

            # EXAMPLE OF ORDER_MARKET_BUY

            # {'clientOrderId': 'ZeKx4wrRZdYL3idkcPbaON',
            # 'cummulativeQuoteQty': '10.84427520',
            # 'executedQty': '0.04800000',
            # 'fills': [{'commission': '0.00003600',
            #            'commissionAsset': 'BNB',
            #            'price': '225.92240000',
            #            'qty': '0.04800000',
            #            'tradeId': 165914884}],
            # 'orderId': 1639119357,
            # 'orderListId': -1,
            # 'origQty': '0.04800000',
            # 'price': '0.00000000',
            # 'side': 'BUY',
            # 'status': 'FILLED',
            # 'symbol': 'BNBUSDT',
            # 'timeInForce': 'GTC',
            # 'transactTime': 1614958605886,
            # 'type': 'MARKET'}

            
            take_profit_price = self.get_take_profit_price(buy_price)
            stop_loss_price = self.get_stop_loss_price(buy_price)
            

            order_oco_sell =  self.client.create_oco_order(
                    symbol=self.symbol,
                    side=SIDE_SELL,
                    stopLimitTimeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    stopLimitPrice = stop_loss_price,
                    stopPrice= round((stop_loss_price*1.000), self.precision),
                    
                    price=take_profit_price)
                    
                

            
            record = {
                'recordId' : order_market_buy['orderId'],
                'recordData': [order_market_buy, order_oco_sell['orderReports']]
            }
            self.orders.append(record)
            self.open_orders.append(record['recordData'])
            
            self._log_temp()
            
            

            # EXAMPLE OF ORDER OCO SELL JSON

            # {'contingencyType': 'OCO',
            # 'listClientOrderId': 'xM4mCPJDxhoLLGBkVKsYt2',
            # 'listOrderStatus': 'EXECUTING',
            # 'listStatusType': 'EXEC_STARTED',
            # 'orderListId': 18376122,
            # 'orderReports': [{'clientOrderId': 'HvmvPgfPLccLBH4ppwM4CW',
            #                   'cummulativeQuoteQty': '0.00000000',
            #                   'executedQty': '0.00000000',
            #                   'orderId': 1639119368,
            #                   'orderListId': 18376122,
            #                   'origQty': '0.04800000',
            #                   'price': '224.02310000',
            #                   'side': 'SELL',
            #                   'status': 'NEW',
            #                   'stopPrice': '224.02310000',
            #                   'symbol': 'BNBUSDT',
            #                   'timeInForce': 'GTC',
            #                   'transactTime': 1614958606001,
            #                   'type': 'STOP_LOSS_LIMIT'},
            #                  {'clientOrderId': 'zfqMnRIjspbaNIoX4NcrM3',
            #                   'cummulativeQuoteQty': '0.00000000',
            #                   'executedQty': '0.00000000',
            #                   'orderId': 1639119369,
            #                   'orderListId': 18376122,
            #                   'origQty': '0.04800000',
            #                   'price': '228.52250000',
            #                   'side': 'SELL',
            #                   'status': 'NEW',
            #                   'symbol': 'BNBUSDT',
            #                   'timeInForce': 'GTC',
            #                   'transactTime': 1614958606001,
            #                   'type': 'LIMIT_MAKER'}],
            # 'orders': [{'clientOrderId': 'HvmvPgfPLccLBH4ppwM4CW',
            #             'orderId': 1639119368,
            #             'symbol': 'BNBUSDT'},
            #            {'clientOrderId': 'zfqMnRIjspbaNIoX4NcrM3',
            #             'orderId': 1639119369,
            #             'symbol': 'BNBUSDT'}],
            # 'symbol': 'BNBUSDT',
            # 'transactionTime': 1614958606001}
            
    def check_current_position2(self, current_price):
        try:
            if self.is_in_position:
                print("checked current position")
                
                for orders in self.open_orders[:]:
                    # LOOP THRU PENDING ORDERS
                    
                    current_open_order = orders[-1]
                    
                    if type(current_open_order) == list and len(current_open_order) > 1:
                        #handle OCO ORDER
                        current_open_order = order[0]
                        
                    #retrieved stop loss order
                    #check for stop loss
                    if current_price <= float(current_open_order['price']):

                        #fetch order from web to check it's status
                        current_stop_loss_order = self.client.get_order(symbol = self.symbol, orderId=current_open_order['orderId'])
                        
                        if current_stop_loss_order['status'] == 'FILLED':
                            # print("STOP LOSS MET!: ", datetime.datetime.fromtimestamp(current_stop_loss_order['transactTime']/1000))
                            print("STOP LOSS MET!: ")
                            pprint.pprint(current_stop_loss_order)
                            #update records
                            
                            orders.pop()
                            orders.append(current_stop_loss_order)
                            
                            #update stake
                            price, qty, vol = self._extract_filled_order(current_stop_loss_order)
                            self.stake = vol
                            
                            #update flag
                            self.is_in_position = False 
                            self.open_orders.remove(orders)
                            return True
                            
        except Exception as e:
            print(".. error occured in 'check_current_position2' inside OrderManager... see below: ")
            print(e)
            
        return False

    def check_current_position(self, current_price):

        if self.is_in_position:
            
            for orders in self.open_orders[:]:
                stop_loss_order, take_profit_order = orders # returns 2 orders 
                
                #check for take profit
                if current_price >= float(take_profit_order['price']):
                    order = self.client.get_order(symbol = self.symbol, orderId=take_profit_order['orderId'])
                    if order['status'] == 'FILLED':
                        price, qty, vol = self._extract_filled_order(take_profit_order)
                        self.stake = vol
                        order['status'] = 'FILLED'
                        self.is_in_position = False
                        del self.open_orders[0]
                        return True
            
                #check for stop loss
                if current_price <= float(stop_loss_order['price']):
                    stop_loss_order = self.client.get_order(symbol = self.symbol, orderId=stop_loss_order['orderId'])
                    if stop_loss_order['status'] == 'FILLED':
                        price, qty, vol = self._extract_filled_order(take_profit_order)
                        self.stake = vol
                        self.orders[-1]['recordData'].append(stop_loss_order)
                        self.is_in_position = False
                        self.was_stop_loss = True
                        del self.open_orders[0]
                        return True
        
        return False
                        
    def trailing_stop(self, current_price):
        
        if self.is_in_position:
            try:
                for orders in self.open_orders[:]:

                    current_stop_loss_order = orders[-1] #stop_loss_order
                    
                    if type(current_stop_loss_order) == list and len(current_stop_loss_order) > 1:
                        #HANDLE CCO ORDER ONLY
                        current_stop_loss_order = current_stop_loss_order[0]
                        
                    print("...retrieved stop loss order...")

                    if orders[0]['symbol'].upper() == self.symbol.upper() and current_price > self.prev_price:

                        #cancel previous stop loss
                        cancel_order = self.client.cancel_order(symbol = self.symbol, orderId = current_stop_loss_order['orderId'])
                        print("...cancelled ... old stop losss")
                        
                        
                            
                        #cautious: need the "qty" only, others are ignored
                        price, qty, vol = self._extract_filled_order(current_stop_loss_order)
                        print("ready to add new stop_loss, prev_price: ", self.prev_price, " current_price: ", current_price)
                        
                        new_order_limit_sell = self.client.create_order(
                            symbol= self.symbol,
                            side=SIDE_SELL,
                            type='STOP_LOSS_LIMIT',
                            timeInForce=TIME_IN_FORCE_GTC,
                            price = round(float(current_stop_loss_order['price']) + (current_price - self.prev_price), self.precision), 
                            stopPrice = round(float(current_stop_loss_order['stopPrice']) + (current_price - self.prev_price), self.precision),
                            quantity= qty,
                            newOrderRespType = 'FULL')
                        
                        pprint.pprint(new_order_limit_sell)
                        print("added new stop_loss, prev_price: ", self.prev_price, " current_price: ", current_price)

                        orders.pop() # pop out current stop loss order
                        orders.append(new_order_limit_sell) # append new stop loss order
                        self.prev_price = current_price # update buy price
                        
                        return True
                        
            except Exception as e:
                print(".. error occured in 'trailing_stop' inside OrderManager... see below: ")
                print(e)
                
        return False
        
    def _extract_filled_order(self, order):

        totalQty = 0
        totalVolume = 0
        avgPrice = 0

        try:
            for i in order['fills']:
                totalQty += float(i['qty'])
                totalVolume += float(i['price'])*float(i['qty'])
            
            avgPrice = math.ceil(totalVolume/totalQty*math.pow(10, self.precision))/ math.pow(10, self.precision)
            return avgPrice, totalQty, round(totalVolume, self.precision)
        
        except:
            return float(order['price']), float(order['origQty']),  round(float(order['price']) * float(order['origQty']), self.precision)

        
        
    def _load_open_orders(self):
        print("load..open..orders")


    def _log_temp(self):


        directory_path = os.path.dirname(os.path.dirname(__file__))

        os.makedirs(directory_path+"\\loggings", exist_ok = True)

        with open(
                os.path.join(directory_path,"loggings\\temp_order_log_.json"),'w', encoding='utf-8') as file:
            json.dump([self.orders, self.open_orders],file)

    def log(self, metadata):

        directory_path = os.path.dirname(os.path.dirname(__file__))

        os.makedirs(directory_path+"\\loggings", exist_ok = True)

        date_time = datetime.datetime.fromtimestamp(round(time.time()))

        path = "loggings\\{symbol}_{year}_{month}_{date}_{hour}_{minute}_{second}_order_log.json".format(
                    symbol=self.symbol, 
                    year = date_time.year,
                    month = date_time.month,
                    date = date_time.day,
                    hour = date_time.hour,
                    minute = date_time.minute,
                    second = date_time.second
                )

        with open(os.path.join(directory_path, path), 'w', encoding='utf-8') as file:
            json.dump([metadata, self.orders],file)

        print("order maker logged")
    
    def _get_decimal_precision(self, symbol):
        
        info = self.client.get_symbol_info(symbol=symbol)
        minPrice = float(info['filters'][0]['minPrice'])
        precision = 0
        
        while minPrice != 1:
            minPrice = minPrice * 10
            precision += 1
        
        return precision
        


    def stop(self):
        #TODO: cancel any
        print("order manager stop")

    def get_config(self):

        return {
            'discount': self.discount,
            'fee': self.fee,
            'stake': self.stake,
            'stopLoss': self.stop_loss,
            'takeProfit': self.take_profit
        }


if __name__ == "__main__":

    pass
    
