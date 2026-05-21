import streamlit as st
import yfinance as yf
import pandas as pd
import time
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide", page_icon="🏆")
st.title("🏆 Jaynish Trading Terminal")

# --- INITIALIZE PORTFOLIO ---
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame(columns=['Ticker', 'Entry Price', 'Quantity'])

# --- MOCK DATA FOR STABILITY ---
ticker_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

# --- SCANNER ---
st.subheader("Live Scanner")
with st.spinner("Fetching market data..."):
    try:
        data = yf.download(ticker_list, period="1mo", group_by='ticker', progress=False)
        results = []
        for t in ticker_list:
            df = data[t].dropna()
            if not df.empty:
                results.append({"Ticker": t.replace(".NS", ""), "Price": round(float(df['Close'].iloc[-1]), 2)})
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.write("No data found.")
    except Exception as e:
        st.error(f"Scanner Error: {e}")

# --- REFRESH ---
if st.button("Refresh Data"):
    st.rerun()
