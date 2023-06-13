import requests
import numpy as np
import pandas as pd
import talib
from binance.client import Client
import config, func
import schedule
from time import sleep
import math

# Đường dẫn tới file .txt chứa danh sách các cặp coin
file_path = 'coin_list_fu.txt'

client = Client(config.API_KEY, config.API_SECRET, testnet=True)

# Đọc danh sách các cặp coin từ file .txt
def read_coin_pairs(file_path):
    coin_pairs = []
    with open(file_path, 'r') as file:
        for line in file:
            coin_pairs.append(line.strip())
    return coin_pairs

# hàm tính khối lượng
def calculate_quantity(coin_pair, usd_value):
    ticker = client.get_ticker(symbol=coin_pair)
    current_price = float(ticker['lastPrice'])
    quantity = usd_value / current_price
    return quantity


# Kiểm tra điều kiện và đặt lệnh cho cặp coin
def place_order_for_coin(coin_pair):
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

    # Tính toán chỉ báo RSI
    rsi = talib.RSI(df['close'], timeperiod=14)
    df['rsi'] = rsi

    # Xác định tín hiệu giao dịch dựa trên RSI
    df['signal'] = np.where(df['rsi'] > 70, -1, np.where(df['rsi'] < 30, 1, 0))

    # Tạo cột tín hiệu dịch chuyển
    df['position'] = df['signal'].diff()


    leverage = 10  # Đòn bẩy
    usdt = 10
    # kiem tra da dat lenh hay chua
    order_status = client.futures_get_open_orders(symbol=coin_pair)
    if len(order_status) > 0:
        print("Lệnh futures đã được đặt: ", coin_pair)
    else:
        # Đặt lệnh futures dựa trên tín hiệu giao dịch
        for i in range(1, len(df)):
            if df['position'].iloc[i] == 1:  # Tín hiệu mua
                price = df['close'].iloc[i]
                quantity = func.calculate_quantity(price, usdt, leverage)
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
                break
            elif df['position'].iloc[i] == -1:  # Tín hiệu bán
                price = df['close'].iloc[i]
                quantity = func.calculate_quantity(price, usdt, leverage)
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

def startTrade():
    # Đọc danh sách các cặp coin
    coin_pairs = read_coin_pairs(file_path)

    # Duyệt qua danh sách các cặp coin và đặt lệnh
    for coin_pair in coin_pairs:
        try:    
            place_order_for_coin(coin_pair)
        except:
            print("khong the dat lenh {}".format(coin_pair))
   

if __name__ == '__main__':
    startTrade()
    # sl_run = 0
    # while True:
    #     startTrade()
    #     sl_run = sl_run + 1
    #     print("Số lần chạy: ", sl_run)
    #     sleep(120)