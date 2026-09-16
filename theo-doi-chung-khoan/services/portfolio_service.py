# add_transaction, get_portfolio_summary.
# Thiết kế: docs/functions/add_transaction.md, docs/functions/get_portfolio_summary.md.

import sqlite3
import pandas as pd

DB_PATH = "data/portfolio.db"


def get_portfolio(user_id):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            symbol,

            SUM(
                CASE
                    WHEN transaction_type = 'BUY'
                    THEN quantity
                    ELSE -quantity
                END
            ) AS quantity,

            SUM(
                CASE
                    WHEN transaction_type = 'BUY'
                    THEN quantity * price
                    ELSE 0
                END
            ) AS total_buy_value,

            SUM(
                CASE
                    WHEN transaction_type = 'BUY'
                    THEN quantity
                    ELSE 0
                END
            ) AS total_buy_quantity

        FROM transactions

        WHERE user_id = ?

        GROUP BY symbol
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(user_id,)
    )

    conn.close()

    if df.empty:
        return df

    df["average_price"] = (
        df["total_buy_value"]
        / df["total_buy_quantity"]
    )

    df = df[df["quantity"] > 0]

    return df
def get_current_market_price(symbol):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT close
        FROM market_prices
        WHERE symbol = ?
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        (symbol,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return float(result[0])

    return 0
import sqlite3
import pandas as pd

DB_PATH = "data/portfolio.db"


def get_current_market_price(symbol):
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT close
        FROM market_prices
        WHERE symbol = ?
        ORDER BY trade_date DESC
        LIMIT 1
        """,
        (symbol,)
    )

    row = cursor.fetchone()

    conn.close()

    return float(row[0]) if row else 0.0


def get_portfolio_summary(user_id):
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
            symbol,
            transaction_type,
            quantity,
            price,
            transaction_date,
            id
        FROM transactions
        WHERE user_id = ?
        ORDER BY transaction_date ASC, id ASC
        """,
        conn,
        params=(user_id,)
    )

    conn.close()

    if df.empty:
        return pd.DataFrame()

    portfolio = {}

    for _, row in df.iterrows():

        symbol = row["symbol"]
        transaction_type = row["transaction_type"]

        quantity = int(row["quantity"])
        price = float(row["price"])

        if symbol not in portfolio:
            portfolio[symbol] = {
                "quantity": 0,
                "cost": 0.0,
                "realized_profit": 0.0
            }

        item = portfolio[symbol]

        # BUY
        if transaction_type == "BUY":

            item["cost"] += quantity * price
            item["quantity"] += quantity

        # SELL
        elif transaction_type == "SELL":

            if item["quantity"] <= 0:
                continue

            average_price = (
                item["cost"] / item["quantity"]
            )

            realized_profit = (
                price - average_price
            ) * quantity

            item["realized_profit"] += realized_profit

            item["cost"] -= (
                average_price * quantity
            )

            item["quantity"] -= quantity

    result = []

    for symbol, item in portfolio.items():

        quantity = item["quantity"]

        if quantity <= 0:
            continue

        average_price = (
            item["cost"] / quantity
        )

        current_price = get_current_market_price(symbol)

        market_value = (
            quantity * current_price
        )

        unrealized_profit = (
            current_price - average_price
        ) * quantity

        unrealized_percent = (
            unrealized_profit
            / item["cost"]
            * 100
            if item["cost"] > 0
            else 0
        )

        result.append(
            {
                "symbol": symbol,
                "quantity": quantity,
                "average_price": average_price,
                "current_price": current_price,
                "cost_value": item["cost"],
                "market_value": market_value,
                "unrealized_profit": unrealized_profit,
                "unrealized_percent": unrealized_percent,
                "realized_profit": item["realized_profit"]
            }
        )

    return pd.DataFrame(result)