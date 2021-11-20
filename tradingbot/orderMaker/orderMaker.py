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

    def __init__(self, client, symbol, stake, take_profit, stop_loss, fee, discount, precision = 4):

        pm.PriceMaker.__init__(self, stake, take_profit, stop_loss, fee, discount, precision)
        self.client = client
        self.symbol = symbol
        self.is_in_position = False
        self.current_position = None
        self.was_stop_loss = False

        self.orders = []


    def buy(self, current_price = 0.00):
        
        if self.is_in_position == True:
            self.check_current_position(current_price)

        if self.is_in_position == False:
            self.is_in_position = True


            order_market_buy = self.client.order_market_buy(
                        symbol= self.symbol.upper(),
                        quoteOrderQty= self.stake)
                        
            buy_price, quantity, volume = self._extract_filled_order(order_market_buy)
            

            record = {
                'recordId' : str(len(self.orders) + 1),
                'recordData': [order_market_buy]
            }

            self.orders.append(record)

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
                    stopPrice= stop_loss_price,
                    
                    price=take_profit_price)

            self.open_orders = order_oco_sell['orderReports'] # the list contains 2 dicts of TP and SL order
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

    def check_current_position(self, current_price):

        stop_loss_order, take_profit_order = self.open_orders # returns 2 orders 
        
        if current_price >= float(take_profit_order['price']):
            take_profit_order = self.client.get_order(symbol = self.symbol, orderId=take_profit_order['orderId'])
            if take_profit_order['status'] == 'FILLED':
                price, qty, vol = self._extract_filled_order(take_profit_order)
                self.stake = vol
                self.orders[-1]['recordData'].append(take_profit_order)
                self.is_in_position = False
                del self.open_orders[0]
                return
        
        if current_price <= float(stop_loss_order['price']):
            stop_loss_order = self.client.get_order(symbol = self.symbol, orderId=stop_loss_order['orderId'])
            if stop_loss_order['status'] == 'FILLED':
                price, qty, vol = self._extract_filled_order(take_profit_order)
                self.stake = vol
                self.orders[-1]['recordData'].append(stop_loss_order)
                self.is_in_position = False
                self.was_stop_loss = True
                del self.open_orders[0]
                return
                    

    def _extract_filled_order(self, order):

        totalQty = 0
        totalVolume = 0
        avgPrice = 0

        for i in order['fills']:
            
            totalQty += float(i['qty'])
            totalVolume += float(i['price'])*float(i['qty'])

        avgPrice = math.ceil(totalVolume/totalQty*10000)/10000
        return avgPrice, totalQty, totalVolume


    def _log_temp(self):


        directory_path = os.path.dirname(os.path.dirname(__file__))

        os.makedirs(directory_path+"\\loggings", exist_ok = True)

        with open(
                os.path.join(directory_path,"loggings\\temp_order_log_.json"),'w', encoding='utf-8') as file:
            json.dump(self.orders,file)

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


    def stop(self):
        #TODO: cancel any
        print("order maker stop")

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
    
