import os
import yfinance as yf
from notion_client import Client
from datetime import datetime

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "JPM", "JNJ",
    "UNH", "V", "PG", "MA", "HD", "XOM", "PFE", "KO", "PEP", "CVX",
    "ABBV", "AVGO", "MRK", "WMT", "DIS", "BAC", "ADBE", "CSCO", "CRM", "NFLX",
    "T", "ABT", "NKE", "ORCL", "MCD", "INTC", "QCOM", "TXN", "TMO", "ACN",
    "COST", "DHR", "NEE", "LLY", "WFC", "BMY", "LIN", "PM", "MDT", "AMGN",
    "UPS", "MS", "LOW", "UNP", "HON", "RTX", "GS", "SBUX", "AMAT", "CVS",
    "IBM", "INTU", "BLK", "BA", "ISRG", "GE", "CAT", "LMT", "NOW", "ZTS",
    "GILD", "DE", "ADI", "BKNG", "PLD", "FIS", "SYK", "SPGI", "MDLZ", "CI",
    "CB", "MO", "MMC", "EW", "C", "EL", "ADI", "ADP", "REGN", "PNC",
    "BDX", "DUK", "TGT", "APD", "SO", "VRTX", "ECL", "AON", "CL", "AEP"
]

def calculate_indicators(ticker_data):
    close = ticker_data["Close"]
    price = round(close[-1], 2)

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = round(100 - (100 / (1 + rs.iloc[-1])), 2)

    macd_line = close.ewm(span=12).mean() - close.ewm(span=26).mean()
    macd = round(macd_line.iloc[-1], 2)

    signal = "Buy" if rsi < 30 and macd > 0 else "Sell" if rsi > 70 and macd < 0 else "Hold"

    return price, rsi, macd, signal

def update_notion(ticker, price, rsi, macd, signal):
    try:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Ticker": {"title": [{"text": {"content": ticker}}]},
                "Price": {"rich_text": [{"text": {"content": str(price)}}]},
                "RSI": {"rich_text": [{"text": {"content": str(rsi)}}]},
                "MACD": {"rich_text": [{"text": {"content": str(macd)}}]},
                "Signal": {"rich_text": [{"text": {"content": signal}}]},
                "Time": {"rich_text": [{"text": {"content": datetime.now().strftime("%Y-%m-%d")}}]}
            }
        )
        print(f"✅ Logged: {ticker} – {signal}")
    except Exception as e:
        print(f"❌ Error logging {ticker}: {e}")

for ticker in tickers:
    try:
        df = yf.download(ticker, period="3mo", interval="1d")
        if not df.empty:
            price, rsi, macd, signal = calculate_indicators(df)
            update_notion(ticker, price, rsi, macd, signal)
    except Exception as error:
        print(f"❌ Failed to process {ticker}: {error}")
