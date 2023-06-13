from binance.client import Client
import config

client = Client(config.API_KEY, config.API_SECRET, testnet=True)

coin_list = []
coin_list_ok = []
usd_value = 10 # 10 dolar

def read_coin_list():
    with open('coin_list.txt', 'r') as file:
        lines = file.readlines()
        for line in lines:
            coin_list.append(line.strip())

def calculate_quantity(coin_pair, usd_value):
    ticker = client.get_ticker(symbol=coin_pair)
    current_price = float(ticker['lastPrice'])
    quantity = usd_value / current_price
    return quantity

# Ví dụ: Tính quantity cho cặp coin BTCUSDT và số USD là 26.8


if __name__ == '__main__':
    print("run")
    read_coin_list()
    for coin in coin_list:
        try:
            quantity = calculate_quantity(coin, usd_value)
            print("coin name: {}".format(coin))
            print("khoi luong: {}".format(quantity))
            coin_list_ok.append(coin)
        except:
            print("coin error: {}".format(coin))
    with open("coin_list_fu.txt", "w") as file:
        for line in coin_list_ok:
            file.write(line + "\n")
