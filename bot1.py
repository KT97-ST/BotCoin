import pandas as pd
from binance.client import Client
from binance.enums import *
from talib import RSI, BBANDS, MACD
import config
# Khóa API và khóa bí mật từ tài khoản Binance của bạn
api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_SECRET_KEY'
client = Client(config.API_KEY, config.API_SECRET, testnet=True)

# Cặp tiền điện tử bạn quan tâm
symbol = 'BTCUSDT'

# Hàm để lấy dữ liệu lịch sử giá từ Binance
def get_historical_data(symbol, interval, limit):
    candles = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

# Hàm để tính toán SMA, RSI và Bollinger Bands
def calculate_indicators(df):
    df['SMA'] = df['close'].rolling(window=14).mean()
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate Bollinger Bands
    high, mid, low = BBANDS(df['close'], timeperiod=20)
    df['BB_high'] = high
    df['BB_mid'] = mid
    df['BB_low'] = low
    
    # Calculate MACD
    macd, signal, hist = MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_signal'] = signal
    return df

# Hàm để đặt lệnh mua với stop-loss và take-profit
def place_buy_order(symbol, quantity, stop_loss, take_profit):
    order = client.create_order(
        symbol=symbol,
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=quantity,
        stopPrice=stop_loss,
        price=take_profit
    )
    return order

# Hàm để đặt lệnh bán với stop-loss và take-profit
def place_sell_order(symbol, quantity, stop_loss, take_profit):
    order = client.create_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=quantity,
        stopPrice=stop_loss,
        price=take_profit
    )
    return order

# Hàm để tính toán số lượng dựa trên số tiền USD và giá hiện tại
def calculate_quantity_usd_to_coin(usd_amount, current_price):
    quantity = usd_amount / current_price
    return quantity

# Lấy giá hiện tại của cặp tiền
def get_current_price(symbol):
    ticker = client.futures_ticker(symbol=symbol)
    current_price = float(ticker['lastPrice'])
    return current_price

# Lấy dữ liệu lịch sử giá và tính toán chỉ số kỹ thuật
data = get_historical_data(symbol, KLINE_INTERVAL_5MINUTE, 100)
data = calculate_indicators(data)

# Vẽ biểu đồ giá và các chỉ số kỹ thuật
# import matplotlib.pyplot as plt

# plt.figure(figsize=(12,5))
# plt.plot(data['timestamp'], data['close'], label='Price')
# plt.plot(data['timestamp'], data['SMA'], label='SMA')
# plt.title('BTC/USDT with SMA')
# plt.legend()
# plt.show()

# plt.figure(figsize=(12,5))
# plt.plot(data['timestamp'], data['RSI'], label='RSI')
# plt.title('BTC/USDT with RSI')
# plt.legend()
# plt.show()

# Định nghĩa chiến lược giao dịch
def strategy(df):
    buy_signals = []
    sell_signals = []
    
    for i in range(2, len(df)):
        if df['RSI'].iloc[i] < 30 and df['RSI'].iloc[i-1] > 30:
            buy_signals.append(df.iloc[i])
        elif df['RSI'].iloc[i] > 70 and df['RSI'].iloc[i-1] < 70:
            sell_signals.append(df.iloc[i])
    return buy_signals, sell_signals

# Thực hiện giao dịch thời gian thực
def real_time_trade(df, usd_amount):
    for i in range(2, len(df)):
        if df['RSI'].iloc[i] < 30 and df['RSI'].iloc[i-1] > 30:
            # Lấy giá hiện tại của cặp tiền
            current_price = get_current_price(symbol)
            
            # Tính toán số lượng dựa trên số tiền USD bạn muốn đầu tư
            quantity = calculate_quantity_usd_to_coin(usd_amount, current_price)
            
            # Thực hiện lệnh mua thời gian thực với stop-loss và take-profit
            try:
                stop_loss = current_price * 0.95
                take_profit = current_price * 1.05
                order = place_buy_order(symbol, quantity, stop_loss, take_profit)
                print("Mua:", order)
            except Exception as e:
                print("Không thể thực hiện lệnh mua:", e)
        elif df['RSI'].iloc[i] > 70 and df['RSI'].iloc[i-1] < 70:
            # Lấy giá hiện tại của cặp tiền
            current_price = get_current_price(symbol)
            
            # Tính toán số lượng dựa trên số tiền USD bạn muốn đầu tư
            quantity = calculate_quantity_usd_to_coin(usd_amount, current_price)
            
            # Thực hiện lệnh bán thời gian thực với stop-loss và take-profit
            try:
                stop_loss = current_price * 1.05
                take_profit = current_price * 0.95
                order = place_sell_order(symbol, quantity, stop_loss, take_profit)
                print("Bán:", order)
            except Exception as e:
                print("Không thể thực hiện lệnh bán:", e)

sl_run = 0
# Bổ sung vào vòng lặp chính của bạn
while True:
    # Lấy dữ liệu giá mới
    try:
        candles = client.futures_klines(symbol=symbol, interval=KLINE_INTERVAL_5MINUTE, limit=100)
        new_data = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        new_data['timestamp'] = pd.to_datetime(new_data['timestamp'], unit='ms')
        new_data['close'] = new_data['close'].astype(float)
        new_data['high'] = new_data['high'].astype(float)
        new_data['low'] = new_data['low'].astype(float)
        data = pd.concat([data, new_data])
        data = calculate_indicators(data)

        sl_run = sl_run + 1
        print("Số lần chạy: ", sl_run)
        # Thực hiện giao dịch thời gian thực với số tiền USD bạn muốn đầu tư
        usd_amount = 10  # Số tiền USD bạn muốn đầu tư
        real_time_trade(data, usd_amount)
    except Exception as e:
        print("Không thể cập nhật dữ liệu:", e)
