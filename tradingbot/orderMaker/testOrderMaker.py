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

        pm.PriceMaker.__init__(self, stake, take_profit, stop_loss, fee, discount, 4)
        self.client = client
        self.symbol = symbol
        self.is_in_position = False
        self.current_position = None

        self.orders = []


    def buy(self, buy_price = 0.00):

        if not self.is_in_position:
            order_market_buy = {'orderId' : str(len(self.orders) + 1), 'price' :  str(buy_price)}

            record = {
                'recordId' : str(len(self.orders) + 1),
                'recordData': [order_market_buy]
            }

            self.orders.append(record)
            self.is_in_position = True

            take_profit_price = self.get_stop_loss_price(buy_price)
            stop_loss_price = self.get_take_profit_price(buy_price)
            order_oco_sell =  {'orderReports' : [{'type' : 'STOP_LOSS_LIMIT', 'price' : str(take_profit_price)}, 
                                    {'type' : 'LIMIT_MAKER', 'price' : str(stop_loss_price)}]}

            self.open_orders = order_oco_sell['orderReports'] # the list contains 2 dicts of TP and SL order
            self._log_temp()

    def check_current_position(self, current_price):

        if self.is_in_position:
            stop_loss_order, take_profit_order = self.open_orders

            if current_price >= float(take_profit_order['price']):
                self.orders[-1]['recordData'].append(take_profit_order)
                self.stake = round(self.stake*(1+self.take_profit),3)
                self.is_in_position = False
                del self.open_orders[0]
                self._log_temp()
                return

            if current_price <= float(stop_loss_order['price']):
                self.orders[-1]['recordData'].append(stop_loss_order)
                self.stake = round(self.stake/(1+self.stop_loss),3)
                self.is_in_position = False
                del self.open_orders[0]
                self._log_temp()
                return
    
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

    def back_test_log(self, metadata):

        directory_path = os.path.dirname(os.path.dirname(__file__))

        os.makedirs(directory_path+"\\test", exist_ok = True)

        date_time = datetime.datetime.fromtimestamp(round(time.time()))

        path = "test\\{symbol}_{year}_{month}_{date}_{hour}_{minute}_{second}_order_log.json".format(
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

        # print("back test order logged")

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
