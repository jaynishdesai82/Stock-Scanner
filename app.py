import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide", page_icon="🏆")
st.title("🏆 Jaynish Trading Terminal")

# --- SETTINGS ---
ticker_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "SBIN.NS"]
volume_multiplier = 1.5

# --- SCANNER ENGINE ---
with st.spinner("Analyzing market momentum..."):
    data = yf.download(ticker_list, period="1y", group_by='ticker', threads=False, progress=False)
    results = []
    
    for t in ticker_list:
        try:
            df = data[t].dropna()
            if df.empty or len(df) < 200: continue
            
            df['50_SMA'] = df['Close'].rolling(window=50).mean()
            df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            vol = float(latest['Volume'])
            vol_sma = float(latest['Vol_SMA'])
            
            # Logic
            trend_ok = (current_price > float(latest['50_SMA']))
            volume_ok = (vol > (vol_sma * volume_multiplier))
            signal = "🚀 BUY SETUP" if (trend_ok and volume_ok) else "⏳ HOLD"
            
            results.append({
                "Ticker": t.replace(".NS", ""),
                "Signal": signal,
                "Price (₹)": round(current_price, 2),
                "RVOL": round(vol / vol_sma, 2)
            })
        except: continue

if results:
    st.table(pd.DataFrame(results))
