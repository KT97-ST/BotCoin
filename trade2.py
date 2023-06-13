import requests
import numpy as np
import pandas as pd
import talib
from binance.client import Client
import config, func
import schedule
from time import sleep

# Đường dẫn tới file .txt chứa danh sách các cặp coin
file_path = 'coin_list_fu.txt'

# client = Client(config.API_KEY, config.API_SECRET, testnet=True)

# Đọc danh sách các cặp coin từ file .txt
def read_coin_pairs(file_path):
    coin_pairs = []
    with open(file_path, 'r') as file:
        for line in file:
            coin_pairs.append(line.strip())
    return coin_pairs

# hàm tính khối lượng
def calculate_quantity(coin_pair, usd_value, client):
    ticker = client.get_ticker(symbol=coin_pair)
    current_price = float(ticker['lastPrice'])
    quantity = usd_value / current_price
    return quantity

# Hàm tính stop loss
def cal_stoploss(price, percent):
    stop_loss_price = price * (1 - percent / 100)
    stop_loss_price = round(stop_loss_price,2)
    return stop_loss_price

# Hàm tính cal_takeprofit
def cal_takeprofit(price, percent):
    take_profit_price = price * (1 + percent / 100)
    take_profit_price = round(take_profit_price,2)
    return take_profit_price

# Kiểm tra điều kiện và đặt lệnh cho cặp coin
def place_order_for_coin(coin_pair):
    client = Client(config.API_KEY, config.API_SECRET, testnet=True)
    # Lấy dữ liệu lịch sử từ Binance
    interval = Client.KLINE_INTERVAL_1HOUR
    limit = 100
    klines = client.futures_klines(symbol=coin_pair, interval=interval, limit=limit)

    # Tạo DataFrame từ dữ liệu lịch sử
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Chuyển đổi dữ liệu sang kiểu số thực
    df = df.astype(float)

    # Tính toán các chỉ báo kỹ thuật
    rsi = talib.RSI(df['close'], timeperiod=14)
    stoch_k, stoch_d = talib.STOCH(df['high'], df['low'], df['close'], fastk_period=1, slowk_period=1, slowd_period=1)
    ema_50 = talib.EMA(df['close'], timeperiod=50)
    ema_200 = talib.EMA(df['close'], timeperiod=200)

    # Xác định tín hiệu giao dịch dựa trên các chỉ báo kỹ thuật
    df['signal'] = np.where((rsi < 30) & (stoch_k < 20) & (stoch_d < 20) & (df['close'] > ema_50) & (ema_50 > ema_200), 1,
                            np.where((rsi > 70) & (stoch_k > 80) & (stoch_d > 80) & (df['close'] < ema_50) & (ema_50 < ema_200), -1, 0))

    # Tạo cột tín hiệu dịch chuyển
    df['position'] = df['signal'].diff()

    # Thiết lập thông số đặt lệnh
    usd_value = 10  # Giá trị USD muốn đặt cho mỗi đồng coin
    # tinh toan ra so luong can dat theo so tien
    quantity = calculate_quantity(coin_pair, usd_value, client)

    # giành cho BTC vì khối lượng của BTC rất nhỏ nên sẽ lấy số thập phân 4 số VD: 0.004 tương đương với 10
    if coin_pair.strip() == "BTCUSDT":
        if quantity > 0.0003:
            quantity = round(quantity, 4)
    else:
        if isinstance(quantity, float):
            quantity = round(quantity, 3)
        else:
            quantity = quantity

    leverage = 10  # Đòn bẩy
    quantity = quantity * leverage
    stop_loss = 0.05  # Mức stop loss (95% giá mua/short)
    take_profit = 1.05  # Mức take profit (105% giá mua/short)
    # kiem tra da dat lenh hay chua
    order_status = client.futures_get_open_orders(symbol=coin_pair)
    if len(order_status) > 0:
        print("Lệnh futures đã được đặt: ", coin_pair)
    else:
        # Đặt lệnh futures dựa trên tín hiệu giao dịch
        for i in range(1, len(df)):
            if df['position'].iloc[i] == 1:  # Tín hiệu mua
                price = df['close'].iloc[i]
                #quantity = func.calculate_quantity(price, 10, leverage)
                stop_loss_price =  func.cal_stoploss(price, 1)
                take_profit_price = func.cal_takeprofit(price, 3)
                if stop_loss_price > price:
                    tmp = stop_loss_price
                    stop_loss_price = take_profit_price
                    take_profit_price = tmp
                print("========================================")
                print("Lệnh BUY: {}".format(coin_pair))
                print("price: {}".format(price))
                print("stop loss price: {}".format(stop_loss_price))
                print("take profit price: {}".format(take_profit_price))
                print("quantity: {}".format(quantity))
                print("leverage: {}".format(leverage))
                print("========================================")
                # Lấy thông tin vị thế hiện tại
                order = client.futures_create_order(symbol=coin_pair,side=Client.SIDE_BUY,type=Client.ORDER_TYPE_MARKET,quantity=quantity,leverage=leverage)
                sleep(1)
                set_stop_loss = client.futures_create_order(symbol=coin_pair, side='SELL', type='STOP_MARKET', quantity=quantity, stopPrice=stop_loss_price)
                print("Đã đặt stop_loss: {}".format(stop_loss_price))
                sleep(1)
                set_take_profit = client.futures_create_order(symbol=coin_pair, side='SELL', type='TAKE_PROFIT_MARKET', quantity=quantity, stopPrice=take_profit_price)
                print("Đã đặt stop_loss: {}".format(take_profit_price))
                print("==========================Break===========")
                # break
            elif df['position'].iloc[i] == -1:  # Tín hiệu bán
                price = df['close'].iloc[i]
                #quantity = func.calculate_quantity(price, 10, leverage)
                stop_loss_price =  func.cal_stoploss(price, 1)
                take_profit_price = func.cal_takeprofit(price, 3)

                if stop_loss_price < price:
                    tmp = stop_loss_price
                    stop_loss_price = take_profit_price
                    take_profit_price = tmp
                print("========================================")
                print("Lệnh SELL: {}".format(coin_pair))
                print("price: {}".format(price))
                print("stop loss price: {}".format(stop_loss_price))
                print("take profit price: {}".format(take_profit_price))
                print("quantity: {}".format(quantity))
                print("leverage: {}".format(leverage))
                print("========================================")
                order = client.futures_create_order(symbol=coin_pair,side=Client.SIDE_SELL,type=Client.ORDER_TYPE_MARKET,quantity=quantity,leverage=leverage)
                sleep(1)           
                set_stop_loss = client.futures_create_order(symbol=coin_pair, side='BUY', type='STOP_MARKET', quantity=quantity, stopPrice=stop_loss_price)
                print("Đã đặt stop_loss: {}".format(take_profit_price))
                sleep(1)
                set_take_profit = client.futures_create_order(symbol=coin_pair, side='BUY', type='TAKE_PROFIT_MARKET', quantity=quantity, stopPrice=take_profit_price)
                print("Đã đặt take_profit: {}".format(stop_loss_price))
                print("=======================Break=============")s
                # break
            # else: 
                # print("Không có lệnh !")


def startTrade():
    # Đọc danh sách các cặp coin
    coin_pairs = read_coin_pairs(file_path)

    # Duyệt qua danh sách các cặp coin và đặt lệnh
    for coin_pair in coin_pairs:
        try:    
            place_order_for_coin(coin_pair)
        except Exception as e:
            print("khong the dat lenh {}".format(e))
   

if __name__ == '__main__':
    sl_run = 0
    while True:
        startTrade()
        sl_run = sl_run + 1
        print("Số lần chạy: ", sl_run)
        sleep(120)