import symbol
import time
from binance.client import Client
import ta
import talib
import numpy as np
import pandas as pd

# Khởi tạo sàn giao dịch (ví dụ: sàn Binance)
# Khởi tạo client của Binance
api_key = 'f4d2418dd892fc6819c13c790029a25af89ade4044cf52f409215ce42fc7bf02'#'YOUR_API_KEY'
api_secret = 'f212db85a51ea8eb67df6ee74b5a480cef95a42693cf1de76d888a4fe9b15a77'#'YOUR_API_SECRET'
#client = Client(api_key, api_secret, futures_type=Client.FUTURES_MODE_ISOLATED)
client = Client(api_key, api_secret, testnet=True)

# Lấy danh sách các cặp đồng coin
exchange_info = client.futures_exchange_info()
symbols = [symbol['symbol'] for symbol in exchange_info['symbols']]
#print(symbols)

# Cặp đồng coin và khoảng thời gian
interval = Client.KLINE_INTERVAL_1MINUTE
#interval = Client.KLINE_INTERVAL_1HOUR
#interval = Client.KLINE_INTERVAL_1DAY



def buy_coin(symbol):
    try:
        # Gọi hàm để lấy giá thị trường hiện tại của cặp giao dịch BTCUSDT
        #ticker = client.get_symbol_ticker(symbol=symbol)
        print("Symbol: ", symbol)  # BTCUSDT

        #current_price = float(ticker['price'])
        #print("current_price:", current_price)

        # Lấy dữ liệu lịch sử giá
        #klines = client.get_klines(symbol=symbol, interval=interval, limit=10)
        #print("lấy dữ liệu lịch sử giá:")
        klines = client.futures_klines(symbol=symbol, interval=interval , limit=100)
        #print("klines:", klines)
        #print(klines[0])
        #print(klines[len(klines)-1])
        #print(klines[len(klines)-2])
        
        # Chỉ lấy giá đóng cửa
        close_prices = [float(kline[4]) for kline in klines]
        #print("close_prices", close_prices)

        # Chỉ lấy khối lượng giao dich
        volume = [float(kline[5]) for kline in klines]
        print("volume: ", volume)

        # Chuyển đổi danh sách thành mảng numpy
        close_prices_np = np.array(close_prices)
        #print("close_prices_np", close_prices_np)
        #print("len(close_prices_np): ", len(close_prices_np))

        # Relative Strength Index (RSI)

        #rsi = talib.RSI(close_prices_np, timeperiod=len(close_prices_np))
        rsi = talib.RSI(close_prices_np)
        #print("rsi",rsi)
        #print("rsi[len(rsi)-1]",rsi[len(rsi)-1])
        #print("rsi[len(rsi)-2]",rsi[len(rsi)-2])

        # Xác định xu hướng
        #if rsi[len(rsi)-1] > rsi[len(rsi)-2] and rsi[len(rsi)-1] < 20:  # RSI < 30 thì được xem là 'quá bán'
        if rsi[len(rsi)-1] < 10:  # RSI < 30 thì được xem là 'quá bán'
            print('RSI đang quá bán, có thể xem xét mua.')
            # Đưa ra lệnh mua
            quantity = round((1000/close_prices_np[len(close_prices_np)-1]),2)  # Thay đổi số lượng mua tùy ý
            if quantity <= 0:
                quantity = 1
            #leverage = client.fget_max_leverage(symbol)  # Lấy đòn bẩy cao nhất của cặp đồng coin
            order = client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity,
                leverage=20
            )
            print('Mua thành công:', order)
        #elif rsi[len(rsi)-1] < rsi[len(rsi)-2] and rsi[len(rsi)-1] > 70:  # RSI > 70 thì được xem là 'quá mua'
        elif rsi[len(rsi)-1] > 90:  # RSI > 70 thì được xem là 'quá mua'
            print('RSI đang quá mua, có thể xem xét bán.')
            # Đưa ra lệnh bán
            print("quantity")
            quantity = round((1000/close_prices_np[len(close_prices_np)-1]),2)  # Thay đổi số lượng mua tùy ý
            if quantity <= 0:
                quantity = 1
            #leverage = client.fget_max_leverage(symbol)  # Lấy đòn bẩy cao nhất của cặp đồng coin
            #print(leverage)
            order = client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity,
                leverage=20
            )
            print('Bán thành công:', order)
        #else:
            #print('RSI đang ở mức bình thường.')

        #exit()
        

    except Exception as e:
        print("Error: ", e)
        return

#buy_coin("BTCUSDT")
    
for symbol in symbols:
    #print("symbol: ", symbol)
    buy_coin(symbol)
    

