import sqlite3

conn = sqlite3.connect('data/portfolio.db')
cursor = conn.cursor()

# Get latest prices from market_prices table
cursor.execute("""
    SELECT symbol, close 
    FROM market_prices 
    WHERE (symbol, trade_date) IN (
        SELECT symbol, MAX(trade_date) FROM market_prices GROUP BY symbol
    )
    ORDER BY symbol
""")

print("📊 Latest market prices:")
prices = {}
for row in cursor.fetchall():
    symbol, price = row
    prices[symbol] = price
    print(f"  {symbol}: {price} VND")

print("\n🚨 Active alerts and whether they would trigger:")
cursor.execute("""
    SELECT a.id, a.symbol, a.target_price, a.condition, a.alert_type, a.is_active
    FROM price_alerts a
    WHERE a.is_active = 1
    ORDER BY a.symbol
""")

for row in cursor.fetchall():
    alert_id, symbol, target_price, condition, alert_type, is_active = row
    current_price = prices.get(symbol, None)
    
    if current_price is None:
        trigger_status = "❌ No price data"
    elif condition == "GREATER_THAN_OR_EQUAL":
        trigger_status = "✓ TRIGGERED" if current_price >= target_price else f"✗ Not yet ({current_price} < {target_price})"
    else:  # LESS_THAN_OR_EQUAL
        trigger_status = "✓ TRIGGERED" if current_price <= target_price else f"✗ Not yet ({current_price} > {target_price})"
    
    print(f"  Alert {alert_id}: {symbol} {condition} {target_price} -> {trigger_status}")

conn.close()
