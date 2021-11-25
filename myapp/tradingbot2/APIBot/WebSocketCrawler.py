import websocket
from pprint import pprint
from datetime import datetime
import json
import time

from ..TradingBot.GenericTradingBot import GenericTradingBot



class WebSocketCrawler(GenericTradingBot):
    def __init__(self):
        super().__init__()
        self.host = "wss://stream.binance.com:9443/ws/"
        self.WS = [
            self.host + "!ticker@arr",
            self.host + "@ticker"
        ]
        self.running = False
        self.active_ws = None
        self.active_url = None

        print("hi im web socket crawler")
              
    
    def _main(self):
        
        def on_message(ws, message):
            dataJson = json.loads(message)
            
            dataJson[0]['E'] = datetime.fromtimestamp(int(dataJson[0]['E'])/1000)
            dataJson[0]['C'] = datetime.fromtimestamp(int(dataJson[0]['C'])/1000)
            dataJson[0]['O'] = datetime.fromtimestamp(int(dataJson[0]['O'])/1000)
            pprint("dataJson[0]")
            # print(self.active_url)

        def on_error(ws, error):
            print(error)

        def on_close(ws, close_status_code, close_msg):
            print("### closed ###")
            
        def on_open(ws):
            print("web socket open")
        
        # websocket.enableTrace(True)
        self.active_ws = websocket.WebSocketApp(self.active_url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
        self.active_ws.run_forever()
        self.running = True
        
        
    def stop(self):
        self.running = False
        self.active_ws.keep_running = False
        print("web socket closed")
        


if __name__ == "__main__":
    a = WebSocketCrawler()
    a.start()
    time.sleep(5)
    a.stop()
    print("HELLO?")
    