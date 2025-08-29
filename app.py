import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests

st.set_page_config(page_title="Growlio - Investment Learning App", layout="wide")

st.title("📈 Growlio: Investment Learning App")

# --- Stock Selection ---
stocks = st.multiselect("Choose Stocks", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"], default=["AAPL"])
period = st.selectbox("Select Period", ["1mo", "3mo", "6mo", "1y", "5y", "max"], index=2)

all_data = {}

for stock in stocks:
    ticker = yf.Ticker(stock)
    data = ticker.history(period=period)
    
    if data.empty:
        st.warning(f"No data found for {stock}")
        continue
    
    # Save for combining later
    all_data[stock] = data["Close"]
    
    # --- Metrics ---
    last_close = data["Close"].iloc[-1]
    prev_close = data["Close"].iloc[-2] if len(data) > 1 else last_close
    pct_change = ((last_close - prev_close) / prev_close) * 100 if prev_close != 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{stock} Last Close", f"${last_close:.2f}")
    with col2:
        st.metric("Change", f"{pct_change:.2f}%")
    with col3:
        st.metric("Volume", f"{data['Volume'].iloc[-1]:,}")
    
    # --- Moving Averages ---
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()
    
    # --- Volatility (Standard Deviation of Returns) ---
    data["Returns"] = data["Close"].pct_change()
    data["Volatility"] = data["Returns"].rolling(window=20).std() * np.sqrt(252)
    
    # --- Plot Prices with Moving Averages ---
    st.subheader(f"📊 {stock} Price & Moving Averages")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data.index, data["Close"], label="Close Price")
    ax.plot(data.index, data["MA20"], label="MA20", linestyle="--")
    ax.plot(data.index, data["MA50"], label="MA50", linestyle="--")
    ax.set_title(f"{stock} Price Chart")
    ax.legend()
    st.pyplot(fig)
    
    # --- Plot Volatility ---
    st.subheader(f"📉 {stock} Volatility")
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(data.index, data["Volatility"], color="red")
    ax.set_title(f"{stock} 20-Day Rolling Volatility")
    st.pyplot(fig)
    
    # --- Buy Signal Example (when MA20 crosses above MA50) ---
    buy_signals = data[(data["MA20"] > data["MA50"]) & (data["MA20"].shift(1) <= data["MA50"].shift(1))]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data.index, data["Close"], label="Close Price")
    ax.scatter(buy_signals.index, buy_signals["Close"], marker="^", color="green", label="Buy Signal")
    ax.legend()
    ax.set_title(f"{stock} Buy Signals (MA Cross)")
    st.pyplot(fig)
    
    # --- News Section ---
    st.subheader(f"📰 Latest News for {stock}")
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={stock}"
        response = requests.get(url)
        if response.status_code == 200:
            news_items = response.json().get("news", [])
            if news_items:
                for article in news_items[:5]:  # show top 5
                    st.markdown(f"- [{article['title']}]({article['link']})")
            else:
                st.write("No recent news found.")
        else:
            st.write("Unable to fetch news at this time.")
    except Exception as e:
        st.error(f"Error fetching news: {e}")

# --- Combined Stocks Performance ---
if all_data:
    combined = pd.DataFrame(all_data)
    st.subheader("📊 Combined Stock Performance")
    st.line_chart(combined)
