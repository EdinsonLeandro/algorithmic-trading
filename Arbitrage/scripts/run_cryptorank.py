import sys, os
import pandas as pd
from datetime import datetime
from pytz import timezone
sys.path.append('../../Python packages')

from custom_functions import run_spider, processing_data, send_info_google_sheet # type:ignore


# ------------------------------ Input data ------------------------------ #
current_time = datetime.now(tz=timezone('US/Eastern'))
current_time = current_time.strftime("%Y-%m-%d_%H-%M")

filename = f'Data/Raw_data/aAll_data/{current_time}.csv'
# filename = f'Data/Raw_data/aAll_data/2024-07-12_18-31.csv'
withdrawal_fees = 'Data/Withdrawal_fees.csv'
credentials = ['ed.leandro.medina@gmail.com', 'ven-BLEMX-2018']

# Binance, Bybit, OKX, Kucoin, HTX, MEXC, Bitget, BitMart, BingX, Lbank, CoinW, P2B, Phemex, BigOne, Poloniex,
# CoinEx, BTSE, Coinsbit, Xeggex, BYDFi
usdt_location = 'BitMart'

min_profit = 0.4

# ------------------------------ Run spider ------------------------------ #
if os.path.exists(filename):
    os.remove(filename)

run_spider('cryptorank', filename, (credentials))


# --------------------------- Processing data ---------------------------- #
wallets = pd.read_csv('Data/Wallets.csv')
wallets['MEMO_TAG'].fillna('', inplace=True)

# Set "Exchange" column to index
for column_name in ['Exchange', 'Cryptocurrency', 'Network']:
    wallets[column_name] = wallets[column_name].str.lower()

output = processing_data(filename, withdrawal_fees, min_profit, current_time, usdt_location, wallets)

send_info_google_sheet(output,
                      "https://docs.google.com/spreadsheets/d/1SV1uBmX--LqyQHrwGzEbU7Z5h_NiIKdVKgkSZYWDldo/edit?usp=sharing",
                      'Data')
