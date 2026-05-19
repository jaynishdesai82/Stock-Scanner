import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Champions Club Multi-Scanner", layout="wide")

st.title("🏆 Champions Club Multi-Stock Scanner")
st.write("Real-time automated multi-stock dashboard tracking institutional momentum setups.")

# 1. Sidebar Configuration
st.sidebar.header("Scanner Settings")

# Default watchlist (You can add or remove stocks here)
default_stocks = "360ONE, ABB, ACC, ADANIENSOL, ADANIENT, ADANIGREEN, ADANIPORTS, ADANIPOWER, ATGL, AWL, ABCAPITAL, ABFRL, ALKEM, AMBUJACEM, APOLLOHOSP, APOLLOTYRE, ASHOKLEY, ASIANPAINT, ASTRAL, AUROPHARMA, AU_SMALL_FINANCE, AXISBANK, BAJAJ-AUTO, BAJAJFINSV, BAJAJHLDNG, BAJFINANCE, BALKRISIND, BANDHANBNK, BANKBARODA, BANKINDIA, BATAINDIA, BERGEPAINT, BEL, BHARATFORG, BHEL, BPCL, BHARTIARTL, BIOCON, BOSCHLTD, BRITANNIA, BSE, CGPOWER, CANBK, CDSL, CENTURYTEX, CESC, CHOLAMFIN, CIPLA, COALINDIA, COCHINSHIP, COFORGE, COLPAL, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DLF, DABUR, DALBHARAT, DEEPAKNITR, DELHIQUERY, DIVISLAB, DIXON, LALPATHLAB, DRREDDY, EICHERMOT, ESCORTS, EXIDEIND, NYKAA, FEDERALBNK, FACT, FORTIS, GMRINFRA, GAIL, GAMMONIND, GLAND, GLENMARK, GODREJCP, GODREJPROP, GRASIM, GUJGASLTD, HAL, HCLTECH, HDFCBANK, HDFCLIFE, HMCL, HFCL, RECLTD, HINDALCO, HINDCOPPER, HINDPETRO, HINDUNILVR, ICICIBANK, ICICIGI, ICICIPRULI, IDBI, IDFCFIRSTB, IRB, ITC, ITI, INDIANB, INDHOTEL, IOC, IRCON, IRFC, INDUSINDBK, INFY, IEIL, IPCALAB, JSWENERGY, JSWSTEEL, JAIBALAJI, JPASSOCIAT, JINDALSTEL, JIOFIN, JUBLFOOD, KEI, KALYANKJIL, KANSAINER, KARURVYSYA, KOTAKBANK, KPITTECH, L&TFH, LT, LTIM, LTTS, LICHSGFIN, LICI, LUPIN, MRF, M&M, M&MFIN, VAIBHAVGBL, MARUTI, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MPF, MOTILALOFS, MPHASIS, MRPL, MUTHOOTFIN, NATCOPHARM, NATIONALUM, NAUKRI, NAVINFLUOR, NESTLEIND, NHPC, NLCINDIA, NMDC, NTPC, OBERREALTY, ONGC, OIL, PAYTM, OFSS, POLICYBAZAR, PAGEIND, PATANJALI, PERSISTENT, PETRONET, PIDILITIND, PEL, PNB, PFC, POWERGRID, PRESTIGE, PVRINOX, RADICO, RVNL, RELIANCE, SAIL, SBICARD, SBILIFE, SJVN, SKFINDIA, SRF, SAFARI, SANSERA, SCHAEFFLER, SHREECEM, SHRIRAMFIN, SIEMENS, SOBHA, SOLARINDS, SONACOMS, SBIN, SUNPHARMA, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATACONSUM, TATAELXSI, TATAMOTORS, TATAPOWER, TATASTEEL, TATATECH, TTML, TECHM, TEJASNET, NIACL, RAMCOCEM, TITAN, TORNTPHARM, TORNTPOWER, TRENT, TRIDENT, TIINDIA, UPL, ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VGUARD, VEDL, VOLTAS, WIPRO, YESBANK, ZOMATO, ZYDUSLIFE"
user_stocks = st.sidebar.text_area("Modify Watchlist (Separate with commas):", default_stocks)

volume_multiplier = st.sidebar.slider("Volume Breakout Multiplier (x SMA)", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss Risk %", 3.0, 8.0, 5.0, 0.5)

# Convert input text into a clean list of NSE tickers
ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]

# Function to analyze a single stock
def analyze_stock(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y")
        if df.empty or len(df) < 200:
            return None
        
        # Strategy calculations
        df['50_SMA'] = df['Close'].rolling(window=50).mean()
        df['200_SMA'] = df['Close'].rolling(window=200).mean()
        df['20_Vol_SMA'] = df['Volume'].rolling(window=20).mean()
        
        latest = df.iloc[-1]
        prev_close = df.iloc[-2]['Close']
        
        current_price = latest['Close']
        current_volume = latest['Volume']
        sma_50 = latest['50_SMA']
        sma_200 = latest['200_SMA']
        vol_sma = latest['20_Vol_SMA']
        
        # Rule Validation
        trend_ok = (current_price > sma_50) and (sma_50 > sma_200)
        volume_ok = current_volume > (vol_sma * volume_multiplier)
        price_ok = current_price > prev_close
        
        # Signal assignment
        if trend_ok and volume_ok and price_ok:
            signal = "🚀 BUY SETUP"
        elif current_price < sma_50:
            signal = "🛑 CASH/SELL"
        else:
            signal = "⏳ HOLD / WATCH"
            
        # Risk management calculations
        sl_price = current_price * (1 - (risk_pct / 100))
        target_3r = current_price * (1 + (risk_pct * 3 / 100))
        
        return {
            "Ticker": ticker_symbol.replace(".NS", ""),
            "Signal": signal,
            "Price (₹)": round(current_price, 2),
            "Vol Multiplier": round(current_volume / vol_sma, 2),
            "50 SMA (₹)": round(sma_50, 2),
            "200 SMA (₹)": round(sma_200, 2),
            "Stop Loss (₹)": round(sl_price, 2),
            "Target 1:3 (₹)": round(target_3r, 2)
        }
    except:
        return None

# 2. Main Dashboard Execution
if st.button("🔄 Refresh Market Data") or 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    
    results = []
    with st.spinner("Scanning the National Stock Exchange live..."):
        for t in ticker_list:
            res = analyze_stock(t)
            if res:
                results.append(res)
                
    if results:
        df_results = pd.DataFrame(results)
        
        # Apply visual coloring to the Signal column for readability
        def color_signals(val):
            if "BUY" in val: return 'background-color: #2ecc71; color: white; font-weight: bold;'
            if "CASH" in val: return 'background-color: #e74c3c; color: white;'
            return 'background-color: #f1c40f; color: black;'
            
        styled_df = df_results.style.map(color_signals, subset=['Signal'])
        
        # Render the master spreadsheet table
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Display summarized highlight boxes
        st.subheader("📋 Quick Action Summary")
        buy_stocks = df_results[df_results['Signal'] == "🚀 BUY SETUP"]['Ticker'].tolist()
        sell_stocks = df_results[df_results['Signal'] == "🛑 CASH/SELL"]['Ticker'].tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"**Stocks Triggering Buy Momentum:** {', '.join(buy_stocks) if buy_stocks else 'None right now'}")
        with col2:
            st.error(f"**Stocks Below 50 SMA (Exit/Avoid):** {', '.join(sell_stocks) if sell_stocks else 'None right now'}")
    else:
        st.warning("No valid data could be retrieved for the specified tickers.")
