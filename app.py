import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# --- OFFICIAL BRANDING ---
st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide")

st.title("🏆 Jaynish Multi-Scanner")
st.write("Real-time automated dashboard tracking institutional momentum setups.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Scanner Settings")

app_mode = st.sidebar.radio(
    "Select Scanner Mode:",
    ["📊 Basic Version (Trend & Volume)", "🔥 Pro Version (Sniper Metrics)"]
)
st.sidebar.markdown("---")

# Strictly Cleaned Nifty 200 Watchlist
default_stocks = "ABB, ACC, ABCAPITAL, ABFRL, ADANIENSOL, ADANIENT, ADANIGREEN, ADANIPORTS, ADANIPOWER, ATGL, AWL, ALKEM, AMBUJACEM, APOLLOHOSP, APOLLOTYRE, ASHOKLEY, ASIANPAINT, ASTRAL, AUBANK, AUROPHARMA, AXISBANK, BSE, BAJAJ-AUTO, BAJAJFINSV, BAJFINANCE, BAJAJHLDNG, BALKRISIND, BANDHANBNK, BANKBARODA, BANKINDIA, MAHABANK, BATAINDIA, BEL, BERGEPAINT, BDL, BHARATFORG, BHEL, BPCL, BHARTIARTL, BIOCON, BOSCHLTD, BRITANNIA, CGPOWER, CANBK, CHOLAMFIN, CIPLA, COALINDIA, COCHINSHIP, COFORGE, COLPAL, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DLF, DABUR, DALBHARAT, DEEPAKNITR, DIVISLAB, DIXON, LALPATHLAB, DRREDDY, EICHERMOT, ESCORTS, EXIDEIND, NYKAA, FEDERALBNK, FACT, FORTIS, GAIL, GMRINFRA, GLAND, GLENMARK, GODREJCP, GODREJPROP, GRASIM, GUJGASLTD, HAL, HCLTECH, HDFCAMC, HDFCBANK, HDFCLIFE, HAVELLS, HEROMOTOCO, HINDALCO, HINDCOPPER, HINDPETRO, HINDUNILVR, ICICIBANK, ICICIGI, ICICIPRULI, ISEC, IDBI, IDFCFIRSTB, ITC, INDIANB, INDHOTEL, IOC, IRCTC, IRFC, IGL, INDUSINDBK, NAUKRI, INFY, IPCALAB, J&KBANK, JINDALSTEL, JIOFIN, JSWENERGY, JSWSTEEL, JUBLFOOD, KALYANKJIL, KANSAINER, KARURVYSYA, KOTAKBANK, KPITTECH, L&TFH, LT, LTIM, LTTS, LICHSGFIN, LICI, LUPIN, MRF, M&M, M&MFIN, MANAPPURAM, MARICO, MARUTI, MAZDOCK, MAXHEALTH, METROPOLIS, MOTILALOFS, MPHASIS, MUTHOOTFIN, NATCOPHARM, NATIONALUM, NAVINFLUOR, NESTLEIND, NHPC, NLCINDIA, NMDC, NTPC, OBERREALTY, ONGC, OIL, OFSS, PAYTM, PIIND, PAGEIND, PATANJALI, PERSISTENT, PETRONET, PIDILITIND, PEL, POLYCAB, POONAWALLA, PFC, POWERGRID, PRESTIGE, PNB, RBLBANK, RADICO, RVNL, RECLTD, RELIANCE, SAIL, SBICARD, SBILIFE, SJVN, SKFINDIA, SRF, MOTHERSON, SHREECEM, SHRIRAMFIN, SIEMENS, SOBHA, SOLARINDS, SONACOMS, SBIN, SUNPHARMA, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATACONSUM, TATAELXSI, TATAMOTORS, TATAPOWER, TATASTEEL, TATATECH, TCS, TECHM, TITAN, TORNTPHARM, TORNTPOWER, TRENT, TRIDENT, TIINDIA, UCOBANK, ULTRACEMCO, UNIONBANK, UBL, MCDOWELL-N, VBL, VEDL, VOLTAS, WIPRO, YESBANK, ZOMATO, ZYDUSLIFE"

user_stocks = st.sidebar.text_area("Watchlist (Separate with commas):", default_stocks, height=150)
volume_multiplier = st.sidebar.slider("Volume Breakout Multiplier (x SMA)", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss Risk %", 3.0, 8.0, 5.0, 0.5)

ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]

# --- DASHBOARD ENGINE ---
if st.button("🔄 Refresh Market Data") or 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    
    results = []
    
    # 1. BATCH DOWNLOAD (Anti-Blocker Engine with threads disabled for Cloud)
    with st.spinner("Downloading entire Nifty 200 data at once... (Bypassing blocks)"):
        data = yf.download(ticker_list, period="1y", group_by='ticker', threads=False, progress=False)
        
    progress_text = f"Analyzing setups using {app_mode.split(' ')[1]}..."
    my_bar = st.progress(0, text=progress_text)
    
    total_stocks = len(ticker_list)
    
    # 2. ANALYSIS LOOP
    for i, t in enumerate(ticker_list):
        try:
            if len(ticker_list) == 1:
                df = data.dropna()
            else:
                df = data[t].dropna()
                
            if df.empty or len(df) < 200:
                continue
            
            # Base Calcs
            df['50_SMA'] = df['Close'].rolling(window=50).mean()
            df['200_SMA'] = df['Close'].rolling(window=200).mean()
            df['20_Vol_SMA'] = df['Volume'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            prev_close = df.iloc[-2]['Close']
            
            current_price = float(latest['Close'])
            current_volume = float(latest['Volume'])
            sma_50 = float(latest['50_SMA'])
            sma_200 = float(latest['200_SMA'])
            vol_sma = float(latest['20_Vol_SMA'])
            
            trend_ok = (current_price > sma_50) and (sma_50 > sma_200)
            volume_ok = current_volume > (vol_sma * volume_multiplier)
            price_ok = current_price > float(prev_close)
            
            sl_price = current_price * (1 - (risk_pct / 100))
            target_3r = current_price * (1 + (risk_pct * 3 / 100))
            
            # PRO MODE
            if "Pro Version" in app_mode:
                delta = df['Close'].diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                rs = up.ewm(com=13, adjust=False).mean() / down.ewm(com=13, adjust=False).mean()
                rsi = float(100 - (100 / (1 + rs)).iloc[-1])
                
                exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                macd = float((exp1 - exp2).iloc[-1])
                signal_line = float((exp1 - exp2).ewm(span=9, adjust=False).mean().iloc[-1])
                
                rsi_bullish = 60 <= rsi <= 75
                macd_bullish = macd > signal_line
                close_to_sma = current_price <= (sma_50 * 1.08) 
                
                if trend_ok and volume_ok and price_ok and rsi_bullish and macd_bullish and close_to_sma:
                    signal = "🔥 SNIPER BUY"
                elif trend_ok and volume_ok and price_ok:
                    signal = "🚀 BASE BUY"
                elif current_price < sma_50:
                    signal = "🛑 CASH/SELL"
                else:
                    signal = "⏳ HOLD"
                    
                results.append({
                    "Ticker": t.replace(".NS", ""),
                    "Signal": signal,
                    "Price (₹)": round(current_price, 2),
                    "RSI": round(rsi, 1),
                    "MACD": "UP 📈" if macd_bullish else "DOWN 📉",
                    "Vol Mult": round(current_volume / vol_sma, 2),
                    "50 SMA (₹)": round(sma_50, 2),
                    "Stop Loss": round(sl_price, 2),
                    "Target": round(target_3r, 2)
                })
                
            # BASIC MODE
            else:
                if trend_ok and volume_ok and price_ok:
                    signal = "🚀 BUY SETUP"
                elif current_price < sma_50:
                    signal = "🛑 CASH/SELL"
                else:
                    signal = "⏳ HOLD"
                    
                results.append({
                    "Ticker": t.replace(".NS", ""),
                    "Signal": signal,
                    "Price (₹)": round(current_price, 2),
                    "Vol Mult": round(current_volume / vol_sma, 2),
                    "50 SMA (₹)": round(sma_50, 2),
                    "200 SMA (₹)": round(sma_200, 2),
                    "Stop Loss": round(sl_price, 2),
                    "Target": round(target_3r, 2)
                })

        except Exception as e:
            continue
            
        my_bar.progress((i + 1) / total_stocks, text=f"Analyzing {t.replace('.NS', '')} ({i+1}/{total_stocks})")
        
    my_bar.empty() 
                
    # 3. DISPLAY TABLE
    if results:
        df_results = pd.DataFrame(results)
        
        def color_signals(val):
            if "SNIPER BUY" in val: return 'background-color: #8e44ad; color: white; font-weight: bold;'
            if "BUY" in val: return 'background-color: #2ecc71; color: white; font-weight: bold;'
            if "CASH" in val: return 'background-color: #e74c3c; color: white;'
            return 'background-color: #f1c40f; color: black;'
            
        styled_df = df_results.style.map(color_signals, subset=['Signal'])
        st.dataframe(styled_df, use_container_width=True, height=600)
    else:
        st.error("Could not fetch data. The market might be closed or API is temporarily down.")
