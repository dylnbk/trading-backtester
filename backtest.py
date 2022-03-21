import numpy as np
import talib as tl
from datetime import datetime
from binance.client import Client
from binance.enums import *


API_KEY, API_SECRET = 123456789, 123456789

# get API key and secret
client = Client(API_KEY, API_SECRET)

# get the last 6 hours of candles from binance
klines = client.futures_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "6 month ago UTC")

# RSI settings
rsi_period = 7
rsi_ob = 0
rsi_os = 0

# SMA
sma_period = 100

# ATR settings
atr_period = 21
atr_multi = 5

# stop settings
s_target_a = 0.5
s_target_b = 15
s_trail_a = 1
s_trail_b = 0.5

l_target_a = 0.5
l_target_b = 15
l_trail_a = 1
l_trail_b = 0.5

# calculate stops
short_target_a = (s_target_a / 100)
short_target_b = (s_target_b / 100)
short_trail_a = (s_trail_a / 100)
short_trail_b = (s_trail_b / 100)

long_target_a = (l_target_a / 100)
long_target_b = (l_target_b / 100)
long_trail_a = (l_trail_a / 100)
long_trail_b = (l_trail_b / 100)

# candle data
closes = []
highs = []        
lows = []
u_band =[]
l_band = []
t_value = []
timestamp = []
consecutive_w = []
consecutive_l = []
roi = []
buy_hold_b = []
earning = []
drawdown_percent = []

count = 0

for x in klines:

    closes.append(float(x[4]))
    highs.append(float(x[2]))        
    lows.append(float(x[3])) 
    timestamp.append(datetime.fromtimestamp(x[0]/1000))

# convert to numpy arrays
np_closes = np.array(closes)
np_highs = np.array(highs)
np_lows = np.array(lows)

# send data to calculate ATR, RSI and SMA values 
atr = tl.ATR(np_highs, np_lows, np_closes, atr_period)
rsi = tl.RSI(np_closes, rsi_period)
sma = tl.SMA(np_closes, sma_period)

# check
check = False

# create decimal numbers
def create_dec(input):

        return (input / 100)

# calculates the trend, returns True / False
def supertrend(h, l, c, a, atr_multiplier=atr_multi):

    global u_band
    global l_band
    global t_value
    global check

    # calculate the upper, lower band and set trend variable
    if check:

        # calculate the upper, lower band and set trend variable
        for x in range(len(h)):

            hl = (h[x] + l[x]) / 2
            upperband = hl + (atr_multiplier * a[x])
            lowerband = hl - (atr_multiplier * a[x])

            # add results to array
            u_band[x] = upperband
            l_band[x] = lowerband
            t_value[x] = True
    
    # create a new bank of data
    else:

        # calculate the upper, lower band and set trend variable
        for x in range(len(h)):

            hl = (h[x] + l[x]) / 2
            upperband = hl + (atr_multiplier * a[x])
            lowerband = hl - (atr_multiplier * a[x])

            # add results to array
            u_band.append(upperband)
            l_band.append(lowerband)
            t_value.append(True)

    check = True 

    # calculate trend band and supertrend signal 
    for current in range(1, len(u_band)):

        previous = current - 1

        # if the close is greater than the upper band, trend is True. price below lower band, trend is False
        if c[current] > u_band[previous]:
            t_value[current] = True
            
        elif c[current] < l_band[previous]:
            t_value[current] = False
        
        # price between bands, trend remains the same
        else:
            t_value[current] = t_value[previous]

            # trend is True and the lower band is decreasing, set lower band to previous value = lower band stays flat
            if t_value[current] and l_band[current] < l_band[previous]:
                l_band[current] = l_band[previous]

            # trend is False and the upper band is increasing, set upper band to previous value = upper band stays flat
            if not t_value[current] and u_band[current] > u_band[previous]:
                u_band[current] = u_band[previous]

    # return True / False
    return t_value[current]

def stop_loss(low_price, high_price, entry_av, in_long, in_short):

    stop_loss = 0

    if in_short:

        # trailing at the set targets
        if low_price < entry_av*(1 - short_target_a) and low_price > entry_av*(1 - short_target_b):
            stop_loss = low_price+(low_price*short_trail_a)
        
        elif low_price < entry_av*(1 - short_target_b):
            stop_loss = low_price+(low_price*short_trail_b)
        
        # minimum stop loss
        else:
            stop_loss = entry_av * 1.1

    elif in_long:

        # trailing at the set targets
        if high_price > entry_av*(1 + long_target_a) and high_price < entry_av*(1 + long_target_b):
            stop_loss = high_price-(high_price*long_trail_a)

        elif high_price > entry_av*(1 + long_target_b):
            stop_loss = high_price-(high_price*long_trail_b)

        # minimum stop loss
        else:
            stop_loss = entry_av * 0.9

    return stop_loss

def profit_loss(pnl):

    if pnl > 0:                        

        return True

    else:

        return False

def backtest(h, l, c, atr):

    supertrend(h, l, c, atr)

    global wins
    global losses
    global balance
    global roi
    global buy_hold_b
    global earning
    global count
    global consecutive_l
    global consecutive_w
    global drawdown_percent

    commision = 0
    asset = 0
    balance = [5000]
    pnl = []
    wins = []
    losses = []
    in_long = False
    in_short = False
    high_price = 0
    low_price = 0
    entry_av = 0

    for current in range(1, len(t_value)):

        previous = current - 1

        if closes[current] > high_price:

            high_price = closes[current]

        elif closes[current] < low_price:

            low_price = closes[current]
        
        if not in_long and not in_short and t_value[previous] != t_value[current]:

            commision = balance[-1] * 0.0005
            asset = (balance[-1] - commision) / closes[current]
            high_price = closes[current]
            low_price = closes[current]
            entry_av = closes[current]

            if t_value[current]:

                in_long = True
            
            else:

                in_short = True
        
        elif in_short:

            total_a = (asset * closes[current])
            commision = (total_a * 0.0005)

            if t_value[previous] != t_value[current]:

                pnl.append((balance[-1] - total_a) - commision)
                total_b = balance[-1] + pnl[-1]

                if profit_loss(pnl[-1]):
                    wins.append(pnl[-1])
                else:
                    losses.append(pnl[-1])

                balance.append(total_b)
                high_price = closes[current]
                commision = balance[-1] * 0.0005
                asset = (balance[-1] - commision) / closes[current]
                entry_av = closes[current]
                in_short = False
                in_long = True

            elif closes[current] > stop_loss(low_price, high_price, entry_av, in_long, in_short):

                pnl.append((balance[-1] - total_a) - commision)
                total_b = balance[-1] + pnl[-1]

                if profit_loss(pnl[-1]):
                    wins.append(pnl[-1])
                else:
                    losses.append(pnl[-1])

                balance.append(total_b)
                in_short = False
            
        elif in_long:

            total_a = (asset * closes[current])
            commision = (total_a * 0.0005)

            if t_value[previous] != t_value[current]:

                pnl.append((total_a - balance[-1]) - commision)
                total_b = balance[-1] + pnl[-1]

                if profit_loss(pnl[-1]):
                    wins.append(pnl[-1])
                else:
                    losses.append(pnl[-1])

                balance.append(total_b)
                low_price = closes[current]
                commision = balance[-1] * 0.0005
                asset = (balance[-1] - commision) / closes[current]
                entry_av = closes[current]
                in_short = True
                in_long = False
            
            elif closes[current] < stop_loss(low_price, high_price, entry_av, in_long, in_short):

                pnl.append((total_a - balance[-1]) - commision)
                total_b = balance[-1] + pnl[-1]

                if profit_loss(pnl[-1]):
                    wins.append(pnl[-1])
                else:
                    losses.append(pnl[-1])

                balance.append(total_b)
                in_long = False
            
    earning.append(balance[-1] - balance[0])
    roi.append(round((earning[-1] / balance[0]) * 100, 2))
    buy_hold_a = closes[-1] - closes[0]
    buy_hold_b.append(round((buy_hold_a / closes[0]) * 100, 2))

    drawdown, prev = [], None

    for i, cur in enumerate(pnl):
        if not prev or (prev > 0) != (cur > 0):
            summation = cur
        else:
            summation = summation + cur
        drawdown.append(summation)
        prev = cur

    consecutive_l.append(min(drawdown))
    consecutive_w.append(max(drawdown)) 

    drawdown_percent.append(round(consecutive_l[-1] / balance[0] * 100, 2))

    count += 1

    print(f"---> Backtest: #{count}")

    return True

def optimize(highs, lows, closes):

    # ATR settings
    global atr_period
    global atr_multi

    # stop settings
    global short_target_a
    global short_target_b 
    global short_trail_a
    global short_trail_b

    global long_target_a
    global long_target_b
    global long_trail_a
    global long_trail_b

    global atr

    atr_p = []
    atr_m = []

    largest = []
    short_s = []
    long_s = []
    short_t = []
    long_t = []

    for x in range(1, 11):
        
        atr_multi = x
        
        for y in range(1, 11):

            atr_period = y

            for z in np.arange(1, 10, 0.5):

                short_target_a = create_dec(round(float(z), 2))
                long_target_a = create_dec(round(float(z), 2))

                for a in np.arange(0, 6, 0.2):

                    short_trail_a = create_dec(round(float(a), 2))
                    long_trail_a = create_dec(round(float(a), 2))

                    short_t.append(short_trail_a * 100)
                    long_t.append(long_trail_a * 100)

                    short_s.append(short_target_a * 100)
                    long_s.append(long_target_a * 100)

                    atr_p.append(atr_period)
                    atr_m.append(atr_multi)
                    atr = tl.ATR(np_highs, np_lows, np_closes, atr_period)
                    backtest(highs, lows, closes, atr)
    
    in_order = sorted(roi, reverse=True)

    for h in in_order:

        for x in range(len(roi)):

            if h == roi[x]:

                largest.append(x)

    l_clean = list(dict.fromkeys(largest))

    for x in range(26, 0, -1):

        print("\n------------------")
        print(f"ATR period: {atr_p[l_clean[x]]}")
        print(f"ATR multiplier: {atr_m[l_clean[x]]}")
        print(f"Short stop: {short_s[l_clean[x]]}%, trail: {short_t[l_clean[x]]}%")
        print(f"Long stop: {long_s[l_clean[x]]}%, trail: {long_t[l_clean[x]]}%")
        print(f"ROI: {roi[l_clean[x]]}%")
        print(f"Risk: {drawdown_percent[l_clean[x]]}%")
        print(f"PNL: ${round(earning[l_clean[x]], 2)}")
        print(f"Drawdown: ${round(consecutive_l[l_clean[x]], 2)}")
        print("------------------\n")

    return True

optimize(highs, lows, closes)