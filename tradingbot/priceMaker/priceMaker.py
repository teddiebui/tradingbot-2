import math

class PriceMaker():

    def __init__(self, stake, take_profit, stop_loss, fee, discount, precision):

        self.stake = stake
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.fee = fee
        self.discount = discount
        self.precision = precision

        print("...price maker created")

    def get_break_even_price(self, buy_price):

        fee = self.fee*(1-self.discount)
        price = buy_price*(1+fee)/(1-fee)
        price = math.ceil(price*math.pow(10,self.precision))/math.pow(10,self.precision) # round up to self.precision
        return price

    def get_take_profit_price(self, buy_price):

        fee = self.fee*(1-self.discount)
        price =buy_price*(1+fee)/(1-fee) + self.take_profit*buy_price/(1-fee)
        price = math.ceil(price*math.pow(10,self.precision))/math.pow(10,self.precision) # round up to self.precision
        return price

    def get_stop_loss_price(self, buy_price):

        fee = self.fee*(1-self.discount)
        price = buy_price*(1+fee)/(1-fee) - self.stop_loss/(1+self.stop_loss)*buy_price/(1-fee)
        price = math.ceil(price*math.pow(10,self.precision))/math.pow(10,self.precision) # round up to self.precision
        return price

if __name__ == "__main__":

    # back testing
    p = PriceMaker(stake=20, 
        take_profit=0.01, 
        stop_loss=0.01, 
        fee=0.001, 
        discount = 0.0,
        precision = 4)

    buy_price = 100

    tp = p.get_take_profit_price(buy_price)
    sl = p.get_stop_loss_price(buy_price)
    print(tp)
    print(sl)
    
    tp_fee = (tp + buy_price) * (p.fee)
    sl_fee = (sl + buy_price) * (p.fee)

    print("tp fee: ", tp_fee)
    print("tp/1.01: ", tp/(1+p.take_profit))
    
    print("sl fee: ", sl_fee)
    print("sl*1.01: ", sl*(1+p.stop_loss))

