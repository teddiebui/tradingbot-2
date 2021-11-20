    # tradingbot
    Here to create a cryptocurrency automated trading bot
    bot được viết bằng python 3.9.2

    Yêu cầu thư viện ngoài:
        - python-binance
        - talib
        - numpy
        - playsound
        - websocket-client
    Hướng dẫn cài đặt thư viện:
        - chạy "pip install python-binance" trên cmd hoặc termina
        - mở link https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib, tìm "ta-lib", tải "TA_Lib‑0.4.19‑cp39‑cp39‑win_amd64.whl" (hoặc bản phù hợp với python của bạn)
    mở cmd tại folder có chứa file này, chạy "pip install <tên-file-vừa-tải>"
        - chạy "pip install numpy"
        - chạy "pip install playsound"
        - chạy "pip install websocket-client"

    Hướng dẫn chạy file:

        - tải cả thư mục về. Giải nén, tạo 1 folder có tên "tradingbot", nhét toàn bộ file vào folder này
        - mở file binanceApi.py, tự sửa lại apiKey và apiSecret --> save lại rồi chạy
        - **lưu ý:** chỉ được chạy program từ file binanceApi, không chạy program từ file python khác
