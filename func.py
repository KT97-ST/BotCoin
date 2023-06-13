import math
import decimal

# cắt số cho dộ dài bằng nhau
def truncate_number(price, sl_tp):
    decimal_places = len(str(price).split('.')[1])
    return round(sl_tp, decimal_places)

# hàm tính khối lượng
def calculate_quantity(price, usd_value, leverage):
    quantity = usd_value / price
    quantity = quantity * leverage
    decimal_places = int(math.log10(price)) + 1  # Số chữ số thập phân của price
    quantity = round(quantity,decimal_places)
    return quantity

# Hàm tính takeprofit
# vd 10% thì percent = 1
def cal_takeprofit(price, percent):
    if price > 1:
        take_profit_price = price * (1 + percent / 100)
        decimal_places = int(math.log10(price)) + 1  # Số chữ số thập phân của price
        take_profit_price = round(take_profit_price, decimal_places)
        return truncate_number(price, take_profit_price)
    else:
        decimal.getcontext().prec = 28  # Số chữ số thập phân tối đa
        decimal_price = decimal.Decimal(str(price))
        decimal_percent = decimal.Decimal(str(percent))
        take_profit_price = decimal_price * (1 + decimal_percent / 100)
        return truncate_number(price, take_profit_price)

#Hàm tính stop loss
def cal_stoploss(price, percent):
    if price > 1:
        stop_loss_price = price * (1 - percent / 100)
        decimal_places = int(math.log10(price)) + 1  # Số chữ số thập phân của price
        stop_loss_price = round(stop_loss_price, decimal_places)
        return truncate_number(price, stop_loss_price)
    else:
        decimal.getcontext().prec = 28  # Số chữ số thập phân tối đa
        decimal_price = decimal.Decimal(str(price))
        decimal_percent = decimal.Decimal(str(percent))
        stop_loss_price = decimal_price * (1 + decimal_percent / 100)
        return truncate_number(price, stop_loss_price)
    
# Đọc danh sách các cặp coin từ file .txt
def read_coin_pairs(file_path):
    coin_pairs = []
    with open(file_path, 'r') as file:
        for line in file:
            coin_pairs.append(line.strip())
    return coin_pairs   
# # price = 266.324
# quan = calculate_quantity(266.324, 10, 10)

# # take_profit = cal_takeprofit(price, 3)
# # stop_loss_price = cal_stoploss(price, 1)
# print("Price:", quan)
# # print("take_profit:", take_profit)
# print("stop_loss_price:", stop_loss_price)