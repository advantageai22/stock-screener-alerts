
import yfinance as yf
import pandas as pd
import streamlit as st
import ta
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="Stock Screener Dashboard", layout="centered")
st.title("📊 Stock Screener with RSI, MACD & Email Alerts")
st.markdown("Real-time Buy 🟢 / Hold 🟡 / Sell 🔴 signals with optional email alerts")

tickers = st.text_input("Enter tickers (comma-separated)", "AAPL, MSFT, TSLA, AMZN, GOOGL")
tickers = [ticker.strip().upper() for ticker in tickers.split(",")]

email_alert = st.checkbox("Enable Email Alerts for Buy Signals")

if email_alert:
    email_sender = st.text_input("Your Email (Gmail)", "")
    email_password = st.text_input("App Password (Gmail)", "", type="password")
    email_recipient = st.text_input("Send Alert To (Email)", "")

results = []

def send_email_alert(subject, body, sender, password, recipient):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"Email failed: {e}")

for ticker in tickers:
    stock = yf.Ticker(ticker)
    df = stock.history(period="6mo")

    if df.empty or len(df) < 50:
        continue

    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
    macd = ta.trend.MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['Signal_Line'] = macd.macd_signal()

    latest = df.iloc[-1]

    if latest['RSI'] < 30 and latest['MACD'] > latest['Signal_Line'] and latest['Close'] > latest['MA20'] > latest['MA50']:
        signal = 'Buy 🟢'
        if email_alert and email_sender and email_password and email_recipient:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = f"BUY SIGNAL: {ticker}"
            body = f"""
            📈 Stock: {ticker}
            💰 Price: {latest['Close']:.2f}
            📊 RSI: {latest['RSI']:.2f}
            🔀 MACD: {latest['MACD']:.2f}
            📬 Time: {timestamp}
            """
            send_email_alert(subject, body, email_sender, email_password, email_recipient)
    elif 30 <= latest['RSI'] <= 70:
        signal = 'Hold 🟡'
    else:
        signal = 'Sell 🔴'

    results.append({
        'Ticker': ticker,
        'Price': round(latest['Close'], 2),
        'RSI': round(latest['RSI'], 2),
        'MACD': round(latest['MACD'], 2),
        'Signal Line': round(latest['Signal_Line'], 2),
        'Signal': signal
    })

if results:
    df_result = pd.DataFrame(results)
    st.dataframe(df_result, use_container_width=True)
else:
    st.warning("No data returned. Please check ticker symbols.")
