from datetime import datetime as dt
def run(candles, indicator):
    try:
        validated, rsi_value = indicator.validate_rsi(candles)
        if validated:
            return True, rsi_value
        return False, rsi_value
    except Exception as e:
        print("...algo_rsi: ", e)
    
    

