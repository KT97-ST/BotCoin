import numpy as np
import pandas as pd
import talib
from binance.client import Client
import config
import schedule
from time import sleep

# Đường dẫn tới file .txt chứa danh sách các cặp coin
file_path = 'coin_list_fu.txt'

# Đọc danh sách các cặp coin từ file .txt
def read_coin_pairs(file_path):
    coin_pairs = []
    with open(file_path, 'r') as file:
        for line in file:
            coin_pairs.append(line.strip())
    return coin_pairs

# Hàm tính khối lượng
def calculate_quantity(coin_pair, usd_value, client):
    ticker = client.get_ticker(symbol=coin_pair)
    current_price = float(ticker['lastPrice'])
    quantity = usd_value / current_price
    return quantity

# Hàm xác định tín hiệu mua bán dựa trên RSI
def calculate_rsi_signal(df, rsi_overbought=70, rsi_oversold=30):
    rsi = talib.RSI(df['close'], timeperiod=14)
    df['rsi'] = rsi
    df['rsi_signal'] = np.where(df['rsi'] > rsi_overbought, -1, np.where(df['rsi'] < rsi_oversold, 1, 0))

# Hàm tính chỉ số Stochastic Oscillator
def calculate_stochastic_oscillator(df, stoch_overbought=80, stoch_oversold=20):
    k, d = talib.STOCH(df['high'], df['low'], df['close'])
    df['stochastic_k'] = k
    df['stochastic_d'] = d
    df['stoch_signal'] = np.where((df['stochastic_k'] > df['stochastic_d']) & (df['stochastic_k'] > stoch_overbought), -1,
                                  np.where((df['stochastic_k'] < df['stochastic_d']) & (df['stochastic_k'] < stoch_oversold), 1, 0))

# Hàm tính Bollinger Bands
def calculate_bollinger_bands(df, bb_window=20, bb_std=2):
    upper, middle, lower = talib.BBANDS(df['close'], timeperiod=bb_window, nbdevup=bb_std, nbdevdn=bb_std)
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower

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
    calculate_rsi_signal(df)
    calculate_stochastic_oscillator(df)
    calculate_bollinger_bands(df)

    # Thiết lập thông số đặt lệnh
    usd_value = 10  # Giá trị USD muốn đặt cho mỗi đồng coin
    quantity = calculate_quantity(coin_pair, usd_value, client)
    leverage = 10  # Đòn bẩy

    # kiểm tra đã đặt lệnh hay chưa
    order_status = client.futures_get_open_orders(symbol=coin_pair)
    if len(order_status) > 0:
        print("Lệnh futures đã được đặt: ", coin_pair)
    else:
        # Đặt lệnh futures dựa trên tín hiệu giao dịch
        for i in range(1, len(df)):
            if df['rsi_signal'].iloc[i] == 1 and df['stoch_signal'].iloc[i] == 1 and df['close'].iloc[i] > df['bb_middle'].iloc[i]:
                # Tín hiệu mua
                price = df['close'].iloc[i]
                stop_loss_price = price * 0.95
                take_profit_price = price * 1.05
                order = client.futures_create_order(symbol=coin_pair, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET, quantity=quantity, leverage=leverage)
                sleep(1)
                set_stop_loss = client.futures_create_order(symbol=coin_pair, side=Client.SIDE_SELL, type=Client.ORDER_TYPE_STOP_MARKET, quantity=quantity, stopPrice=stop_loss_price)
                sleep(1)
                set_take_profit = client.futures_create_order(symbol=coin_pair, side=Client.SIDE_SELL, type=Client.ORDER_TYPE_TAKE_PROFIT_MARKET, quantity=quantity, stopPrice=take_profit_price)
                break
            elif df['rsi_signal'].iloc[i] == -1 and df['stoch_signal'].iloc[i] == -1 and df['close'].iloc[i] < df['bb_middle'].iloc[i]:
                # Tín hiệu bán
                price = df['close'].iloc[i]
                stop_loss_price = price * 1.05
                take_profit_price = price * 0.95
                order = client.futures_create_order(symbol=coin_pair, side=Client.SIDE_SELL, type=Client.ORDER_TYPE_MARKET, quantity=quantity, leverage=leverage)
                sleep(1)
                set_stop_loss = client.futures_create_order(symbol=coin_pair, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_STOP_MARKET, quantity=quantity, stopPrice=stop_loss_price)
                sleep(1)
                set_take_profit = client.futures_create_order(symbol=coin_pair, side=Client.SIDE_BUY, type=Client.ORDER_TYPE_TAKE_PROFIT_MARKET, quantity=quantity, stopPrice=take_profit_price)
                break

def startTrade():
    # Đọc danh sách các cặp coin
    coin_pairs = read_coin_pairs(file_path)

    # Duyệt qua danh sách các cặp coin và đặt lệnh
    for coin_pair in coin_pairs:
        try:
            place_order_for_coin(coin_pair)
        except Exception as e:
            print("Không thể đặt lệnh cho {}: {}".format(coin_pair, e))

if __name__ == '__main__':
    sl_run = 0
    while True:
        startTrade()
        sl_run = sl_run + 1
        print("Số lần chạy: ", sl_run)
        sleep(10)
