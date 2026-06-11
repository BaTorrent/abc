from flask import Flask, render_template, jsonify
import ccxt

app = Flask(__name__)

# ২২টি এক্সচেঞ্জের তালিকা
EXCHANGE_IDS = [
    'binance', 'bybit', 'kucoin', 'kraken', 'okx', 'bitget',
    'gate', 'mexc', 'htx', 'bingx', 'coinbase', 'crypto',
    'bitfinex', 'coinex', 'bitmart', 'phemex', 'ascendex',
    'whitebit', 'poloniex', 'lbank', 'digifinex', 'xt'
]

exchanges = {}
for exc_id in EXCHANGE_IDS:
    try:
        exchanges[exc_id] = getattr(ccxt, exc_id)()
    except AttributeError:
        continue

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def get_arbitrage_data():
    symbol = 'SOL/USDT'
    TRADE_AMOUNT_USD = 500.0
    AVERAGE_TRADING_FEE_RATE = 0.001
    FIXED_WITHDRAWAL_FEE_IN_COIN = 0.01

    prices = {}
    for name, exchange in exchanges.items():
        try:
            # কম সময়ে ডাটা লোড করার জন্য টাইমআউট সেট করা ভালো
            exchange.timeout = 3000
            ticker = exchange.fetch_ticker(symbol)
            prices[name] = {
                'buy_at': ticker['ask'],
                'sell_at': ticker['bid']
            }
        except Exception:
            continue

    if len(prices) < 2:
        return jsonify({"status": "error", "message": "Not enough exchange data"})

    best_buy_exchange = min(prices, key=lambda x: prices[x]['buy_at'])
    lowest_buy_price = prices[best_buy_exchange]['buy_at']

    best_sell_exchange = max(prices, key=lambda x: prices[x]['sell_at'])
    highest_sell_price = prices[best_sell_exchange]['sell_at']

    # আর্বিট্রেজ ক্যালকুলেশন লজিক
    coins_bought = TRADE_AMOUNT_USD / lowest_buy_price
    buy_trading_fee = TRADE_AMOUNT_USD * AVERAGE_TRADING_FEE_RATE
    withdrawal_fee_usd = FIXED_WITHDRAWAL_FEE_IN_COIN * lowest_buy_price

    coins_remaining = coins_bought - FIXED_WITHDRAWAL_FEE_IN_COIN
    gross_sell_value_usd = coins_remaining * highest_sell_price
    sell_trading_fee = gross_sell_value_usd * AVERAGE_TRADING_FEE_RATE

    final_received_usd = gross_sell_value_usd - sell_trading_fee - buy_trading_fee
    net_profit_usd = final_received_usd - TRADE_AMOUNT_USD
    net_profit_percentage = (net_profit_usd / TRADE_AMOUNT_USD) * 100

    return jsonify({
        "status": "success",
        "best_buy": best_buy_exchange,
        "buy_price": lowest_buy_price,
        "best_sell": best_sell_exchange,
        "sell_price": highest_sell_price,
        "withdrawal_fee": withdrawal_fee_usd,
        "trading_fees": buy_trading_fee + sell_trading_fee,
        "net_profit_usd": net_profit_usd,
        "net_profit_pct": net_profit_percentage,
        "all_prices": prices  # টেবিলে প্রদর্শনের জন্য সব এক্সচেঞ্জের লাইভ প্রাইস পাঠানো হলো
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)