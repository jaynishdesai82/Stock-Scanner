import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide", page_icon="🏆")
st.title("🏆 Jaynish Trading Terminal")

# --- INITIALIZE PORTFOLIO ---
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame(columns=['Ticker', 'Entry Price', 'Quantity', 'Status'])

# --- TABS ---
tab_scanner, tab_portfolio = st.tabs(["🎯 Live Market Scanner", "💼 Active Ledger"])

# --- SETTINGS ---
ticker_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "SBIN.NS"]
volume_multiplier = 1.5

# --- SCANNER TAB ---
with tab_scanner:
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
                
                trend_ok = (float(latest['Close']) > float(latest['50_SMA']))
                volume_ok = (float(latest['Volume']) > (float(latest['Vol_SMA']) * volume_multiplier))
                signal = "🚀 BUY SETUP" if (trend_ok and volume_ok) else "⏳ HOLD"
                
                results.append({"Ticker": t.replace(".NS", ""), "Signal": signal, "Price (₹)": round(float(latest['Close']), 2), "RVOL": round(float(latest['Volume']) / float(latest['Vol_SMA']), 2)})
            except: continue
            
        if results:
            df_results = pd.DataFrame(results)
            st.table(df_results)
            
            # Paper Trade Button
            st.subheader("Add to Portfolio")
            sel_ticker = st.selectbox("Select Ticker:", df_results['Ticker'].tolist())
            entry = st.number_input("Entry Price:", value=0.0)
            qty = st.number_input("Quantity:", value=100)
            if st.button("Add to Ledger"):
                new_trade = pd.DataFrame([{'Ticker': sel_ticker, 'Entry Price': entry, 'Quantity': qty, 'Status': 'Open'}])
                st.session_state['portfolio'] = pd.concat([st.session_state['portfolio'], new_trade], ignore_index=True)
                st.success(f"Added {sel_ticker} to ledger!")

# --- PORTFOLIO TAB ---
with tab_portfolio:
    st.header("💼 Active Ledger")
    if not st.session_state['portfolio'].empty:
        st.table(st.session_state['portfolio'])
    else:
        st.write("No active trades.")
