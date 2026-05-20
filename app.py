import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Champions Club Multi-Scanner", layout="wide")

st.title("🏆 Champions Club Multi-Stock Scanner (Pro Version)")
st.write("Real-time automated multi-stock dashboard tracking institutional momentum and short-term sniper setups.")

# 1. Sidebar Configuration
st.sidebar.header("Scanner Settings")

# Default Nifty 200 Watchlist
default_stocks = "360ONE, ABB, ACC, ADANIENSOL, ADANIENT, ADANIGREEN, ADANIPORTS, ADANIPOWER, ATGL, AWL, ABCAPITAL, ABFRL, ALKEM, AMBUJACEM, APOLLOHOSP, APOLLOTYRE, ASHOKLEY, ASIANPAINT, ASTRAL, AUROPHARMA, AU_SMALL_FINANCE, AXISBANK, BAJAJ-AUTO, BAJAJFINSV, BAJAJHLDNG, BAJFINANCE, BALKRISIND, BANDHANBNK, BANKBARODA, BANKINDIA, BATAINDIA, BERGEPAINT, BEL, BHARATFORG, BHEL, BPCL, BHARTIARTL, BIOCON, BOSCHLTD, BRITANNIA, BSE, CGPOWER, CANBK, CDSL, CENTURYTEX, CESC, CHOLAMFIN, CIPLA, COALINDIA, COCHINSHIP, COFORGE, COLPAL, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DLF, DABUR, DALBHARAT, DEEPAKNITR, DELHIQUERY, DIVISLAB, DIXON, LALPATHLAB, DRREDDY, EICHERMOT, ESCORTS, EXIDEIND, NYKAA, FEDERALBNK, FACT, FORTIS, GMRINFRA, GAIL, GAMMONIND, GLAND, GLENMARK, GODREJCP, GODREJPROP, GRASIM, GUJGASLTD, HAL, HCLTECH, HDFCBANK, HDFCLIFE, HMCL, HFCL, RECLTD, HINDALCO, HINDCOPPER, HINDPETRO, HINDUNILVR, ICICIBANK, ICICIGI, ICICIPRULI, IDBI, IDFCFIRSTB, IRB, ITC, ITI, INDIANB, INDHOTEL, IOC, IRCON, IRFC, INDUSINDBK, INFY, IEIL, IPCALAB, JSWENERGY, JSWSTEEL, JAIBALAJI, JPASSOCIAT, JINDALSTEL, JIOFIN, JUBLFOOD, KEI, KALYANKJIL, KANSAINER, KARURVYSYA, KOTAKBANK, KPITTECH, L&TFH, LT, LTIM, LTTS, LICHSGFIN, LICI, LUPIN, MRF, M&M, M&MFIN, VAIBHAVGBL, MARUTI, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MPF, MOTILALOFS, MPHASIS, MRPL, MUTHOOTFIN, NATCOPHARM, NATIONALUM, NAUKRI, NAVINFLUOR, NESTLEIND, NHPC, NLCINDIA, NMDC, NTPC, OBERREALTY, ONGC, OIL, PAYTM, OFSS, POLICYBAZAR, PAGEIND, PATANJALI, PERSISTENT, PETRONET, PIDILITIND, PEL, PNB, PFC, POWERGRID, PRESTIGE, PVRINOX, RADICO, RVNL, RELIANCE, SAIL, SBICARD, SBILIFE, SJVN, SKFINDIA, SRF, SAFARI, SANSERA, SCHAEFFLER, SHREECEM, SHRIRAMFIN, SIEMENS, SOBHA, SOLARINDS, SONACOMS, SBIN, SUNPHARMA, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATACONSUM, TATAELXSI, TATAMOTORS, TATAPOWER, TATASTEEL, TATATECH, TTML, TECHM, TEJASNET, NIACL, RAMCOCEM, TITAN, TORNTPHARM, TORNTPOWER, TRENT, TRIDENT, TIINDIA, UPL, ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VGUARD, VEDL, VOLTAS, WIPRO, YESBANK, ZOMATO, ZYDUSLIFE"

user_stocks = st.sidebar.text_area("Watchlist (Separate with commas):", default_stocks, height=150)

volume_multiplier = st.sidebar.slider("Volume Breakout Multiplier (x SMA)", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss Risk %", 3.0, 8.0, 5.0, 0.5)

ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]

# Function to analyze a single stock
def analyze_stock(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y")
        if df.empty or len(df) < 200:
            return None
        
        # 1. Base Strategy calculations
        df['50_SMA'] = df['Close'].rolling(window=50).mean()
        df['200_SMA'] = df['Close'].rolling(window=200).mean()
        df['20_Vol_SMA'] = df['Volume'].rolling(window=20).mean()
        
        # 2. RSI Calculation (14-day)
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 3. MACD Calculation
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        latest = df.iloc[-1]
        prev_close = df.iloc[-2]['Close']
        
        current_price = latest['Close']
        current_volume = latest['Volume']
        sma_50 = latest['50_SMA']
        sma_200 = latest['200_SMA']
        vol_sma = latest['20_Vol_SMA']
        rsi = latest['RSI']
        macd = latest['MACD']
        signal_line = latest['Signal_Line']
        
        # Rule Validation
        trend_ok = (current_price > sma_50) and (sma_50 > sma_200)
        volume_ok = current_volume > (vol_sma * volume_multiplier)
        price_ok = current_price > prev_close
        
        # Short-Term Sniper Filters
        rsi_bullish = 60 <= rsi <= 75
        macd_bullish = macd > signal_line
        close_to_sma = current_price <= (sma_50 * 1.08) # Max 8% away from 50 SMA
        
        # Signal assignment
        if trend_ok and volume_ok and price_ok and rsi_bullish and macd_bullish and close_to_sma:
            signal = "🔥 SNIPER BUY"
        elif trend_ok and volume_ok and price_ok:
            signal = "🚀 BASE BUY"
        elif current_price < sma_50:
            signal = "🛑 CASH/SELL"
        else:
            signal = "⏳ HOLD / WATCH"
            
        sl_price = current_price * (1 - (risk_pct / 100))
        target_3r = current_price * (1 + (risk_pct * 3 / 100))
        
        return {
            "Ticker": ticker_symbol.replace(".NS", ""),
            "Signal": signal,
            "Price (₹)": round(current_price, 2),
            "RSI": round(rsi, 1),
            "MACD Trend": "UP 📈" if macd_bullish else "DOWN 📉",
            "Vol Mult": round(current_volume / vol_sma, 2),
            "50 SMA (₹)": round(sma_50, 2),
            "Stop Loss (₹)": round(sl_price, 2),
            "Target (₹)": round(target_3r, 2)
        }
    except:
        return None

# 2. Main Dashboard Execution
if st.button("🔄 Refresh Market Data") or 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    
    results = []
    
    # Progress Bar UI
    progress_text = "Fetching live data from NSE. Please wait..."
    my_bar = st.progress(0, text=progress_text)
    
    total_stocks = len(ticker_list)
    for i, t in enumerate(ticker_list):
        res = analyze_stock(t)
        if res:
            results.append(res)
        # Update progress bar
        my_bar.progress((i + 1) / total_stocks, text=f"Scanning {t.replace('.NS', '')} ({i+1}/{total_stocks})")
        
    my_bar.empty() # Clear progress bar when done
                
    if results:
        df_results = pd.DataFrame(results)
        
        # Apply visual coloring
        def color_signals(val):
            if "SNIPER BUY" in val: return 'background-color: #8e44ad; color: white; font-weight: bold;'
            if "BASE BUY" in val: return 'background-color: #2ecc71; color: white; font-weight: bold;'
            if "CASH" in val: return 'background-color: #e74c3c; color: white;'
            return 'background-color: #f1c40f; color: black;'
            
        styled_df = df_results.style.map(color_signals, subset=['Signal'])
        
        # Render table
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Display summary boxes
        st.subheader("📋 Quick Action Summary")
        sniper_stocks = df_results[df_results['Signal'] == "🔥 SNIPER BUY"]['Ticker'].tolist()
        buy_stocks = df_results[df_results['Signal'] == "🚀 BASE BUY"]['Ticker'].tolist()
        sell_stocks = df_results[df_results['Signal'] == "🛑 CASH/SELL"]['Ticker'].tolist()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**🔥 Sniper Setups:**<br>{', '.join(sniper_stocks) if sniper_stocks else 'None right now'}")
        with col2:
            st.success(f"**🚀 Base Breakouts:**<br>{', '.join(buy_stocks) if buy_stocks else 'None right now'}")
        with col3:
            st.error(f"**🛑 Sell / Weakness:**<br>{', '.join(sell_stocks) if sell_stocks else 'None right now'}")
    else:
        st.warning("No valid data could be retrieved for the specified tickers.")
