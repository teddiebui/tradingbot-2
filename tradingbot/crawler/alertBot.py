import playsound
import os
import time
import threading

class AlertBot:

    def __init__(self):
        self.thread = None
        pass
    def _run(self):
        try:
            path = os.path.dirname(__file__) + "\\alert.m4a"
            playsound.playsound(path)
            self.thread = None
        except Exception as e:
            print(e)
    
    def alert(self):
        if self.thread == None:
            self.thread = threading.Thread(target=self._run, args=())
            self.thread.start()

if __name__ == "__main__":

    # back testing
    
    a = AlertBot()
    a.run()
