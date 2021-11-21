import os
import pprint
import json
import datetime
class BackTestOneTimeCrawler:
    def __init__(self):
        pass
        self.symbols = set()
    def run(self):
        ## list dir
        path = r'C:\Users\teddi\Desktop\temp\tradingbot-2\myapp\tradingbot2\jsondata\klines'
        files = os.listdir(path)
        count = 0
        
        for i in files:

            _path = path + "\\" + i
            
            symbol = os.path.basename(_path).replace(".json","")

            with open(_path, "r") as f:
                data = json.load(f)

            self.time_pointer = int(data[0][0]/1000)

            for kline in data[1:]:
                time =  int(kline[0]/1000)  
                

                if not self.consecutive(time):
                    print(symbol, datetime.datetime.fromtimestamp(self.time_pointer), datetime.datetime.fromtimestamp(time))   
                    self.symbols.add(symbol)         

                
                # if not self.consecutive(time):
                    
                #     count += 1
                
                self.time_pointer = time
        
        pprint.pprint(self.symbols)
        print("done")

    def consecutive(self, time):
        flag = time - 15*60 == self.time_pointer
        if not flag:
            print("not consecutive: ", flag)
        return flag

    




if __name__ == "__main__":
    b = BackTestOneTimeCrawler()
    b.run()