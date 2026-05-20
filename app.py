import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Champions Club Multi-Scanner", layout="wide")

st.title("🏆 Champions Club Multi-Stock Scanner")
st.write("Real-time automated dashboard tracking institutional momentum setups.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Scanner Settings")

# The Version Toggle!
app_mode = st.sidebar.radio(
    "Select Scanner Mode:",
    ["📊 Basic Version (Trend & Volume)", "🔥 Pro Version (Sniper Metrics)"]
)
st.sidebar.markdown("---")

# Default Nifty 200 Watchlist
default_stocks = "360ONE, ABB, ACC, ADANIENSOL, ADANIENT, ADANIGREEN, ADANIPORTS, ADANIPOWER, ATGL, AWL, ABCAPITAL, ABFRL, ALKEM, AMBUJACEM, APOLLOHOSP, APOLLOTYRE, ASHOKLEY, ASIANPAINT, ASTRAL, AUROPHARMA, AU_SMALL_FINANCE, AXISBANK, BAJAJ-AUTO, BAJAJFINSV, BAJAJHLDNG, BAJFINANCE, BALKRISIND, BANDHANBNK, BANKBARODA, BANKINDIA, BATAINDIA, BERGEPAINT, BEL, BHARATFORG, BHEL, BPCL, BHARTIARTL, BIOCON, BOSCHLTD, BRITANNIA, BSE, CGPOWER, CANBK, CDSL, CENTURYTEX, CESC, CHOLAMFIN, CIPLA, COALINDIA, COCHINSHIP, COFORGE, COLPAL, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DLF, DABUR, DALBHARAT, DEEPAKNITR, DELHIQUERY, DIVISLAB, DIXON, LALPATHLAB, DRREDDY, EICHERMOT, ESCORTS, EXIDEIND, NYKAA, FEDERALBNK, FACT, FORTIS, GMRINFRA, GAIL, GAMMONIND, GLAND, GLENMARK, GODREJCP, GODREJPROP, GRASIM, GUJGASLTD, HAL, HCLTECH, HDFCBANK, HDFCLIFE, HMCL, HFCL, RECLTD, HINDALCO, HINDCOPPER, HINDPETRO, HINDUNILVR, ICICIBANK, ICICIGI, ICICIPRULI, IDBI, IDFCFIRSTB, IRB, ITC, ITI, INDIANB, INDHOTEL, IOC, IRCON, IRFC, INDUSINDBK, INFY, IEIL, IPCALAB, JSWENERGY, JSWSTEEL, JAIBALAJI, JPASSOCIAT, JINDALSTEL, JIOFIN, JUBLFOOD, KEI, KALYANKJIL, KANSAINER, KARURVYSYA, KOTAKBANK, KPITTECH, L&TFH, LT, LTIM, LTTS, LICHSGFIN, LICI, LUPIN, MRF, M&M, M&MFIN, VAIBHAVGBL, MARUTI, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MPF, MOTILALOFS, MPHASIS, MRPL, MUTHOOTFIN, NATCOPHARM, NATIONALUM, NAUKRI, NAVINFLUOR, NESTLEIND, NHPC, NLCINDIA, NMDC, NTPC, OBERREALTY, ONGC, OIL, PAYTM, OFSS, POLICYBAZAR, PAGEIND, PATANJALI, PERSISTENT, PETRONET, PIDILITIND, PEL, PNB, PFC, POWERGRID, PRESTIGE, PVRINOX, RADICO, RVNL, RELIANCE, SAIL, SBICARD, SBILIFE, SJVN, SKFINDIA, SRF, SAFARI, SANSERA, SCHAEFFLER, SHREECEM, SHRIRAMFIN, SIEMENS, SOBHA, SOLARINDS, SONACOMS, SBIN, SUNPHARMA, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATACONSUM, TATAELXSI, TATAMOTORS, TATAPOWER, TATASTEEL, TATATECH, TTML, TECHM, TEJASNET, NIACL, RAMCOCEM, TITAN, TORNTPHARM, TORNTPOWER, TRENT, TRIDENT, TIINDIA, UPL, ULTRACEMCO, UNIONBANK, UNITDSPR, VBL, VGUARD, VEDL, VOLTAS, WIPRO, YESBANK, ZOMATO, ZYDUSLIFE"

user_stocks = st.sidebar.text_area("Watchlist (Separate with commas):", default_stocks, height=150)
volume_multiplier = st.sidebar.slider("Volume Breakout Multiplier (x SMA)", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss Risk %", 3.0, 8.0, 5.0, 0.5)

ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]

# --- SCANNER ENGINE ---
def analyze_stock(ticker_symbol, mode):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y")
        if df.empty or len(df) < 200:
            return None
        
        # Base Calcs
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
        
        # Base Rules
        trend_ok = (current_price > sma_50) and (sma_50 > sma_200)
        volume_ok = current_volume > (vol_sma * volume_multiplier)
        price_ok = current_price > prev_close
        
        sl_price = current_price * (1 - (risk_pct / 100))
        target_3r = current_price * (1 + (risk_pct * 3 / 100))
        
        # PRO MODE CALCS & LOGIC
        if "Pro Version" in mode:
            delta = df['Close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            rs = up.ewm(com=13, adjust=False).mean() / down.ewm(com=13, adjust=False).mean()
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = (exp1 - exp2).iloc[-1]
            signal_line = (exp1 - exp2).ewm(span=9, adjust=False).mean().iloc[-1]
            
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
                signal = "⏳ HOLD / WATCH"
                
            return {
                "Ticker": ticker_symbol.replace(".NS", ""),
                "Signal": signal,
                "Price (₹)": round(current_price, 2), # Explicitly anchored
                "RSI": round(rsi, 1),
                "MACD": "UP 📈" if macd_bullish else "DOWN 📉",
                "Vol Mult": round(current_volume / vol_sma, 2),
                "50 SMA (₹)": round(sma_50, 2),
                "Stop Loss": round(sl_price, 2),
                "Target": round(target_3r, 2)
            }
            
        # BASIC MODE LOGIC
        else:
            if trend_ok and volume_ok and price_ok:
                signal = "🚀 BUY SETUP"
            elif current_price < sma_50:
                signal = "🛑 CASH/SELL"
            else:
                signal = "⏳ HOLD / WATCH"
                
            return {
                "Ticker": ticker_symbol.replace(".NS", ""),
                "Signal": signal,
                "Price (₹)": round(current_price, 2), # Explicitly anchored
                "Vol Mult": round(current_volume / vol_sma, 2),
                "50 SMA (₹)": round(sma_50, 2),
                "200 SMA (₹)": round(sma_200, 2),
                "Stop Loss": round(sl_price, 2),
                "Target": round(target_3r, 2)
            }

    except Exception:
        return None

# --- DASHBOARD UI ---
if st.button("🔄 Refresh Market Data") or 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    
    results = []
    progress_text = f"Scanning Nifty 200 using {app_mode.split(' ')[1]}..."
    my_bar = st.progress(0, text=progress_text)
    
    total_stocks = len(ticker_list)
    for i, t in enumerate(ticker_list):
        res = analyze_stock(t, app_mode)
        if res:
            results.append(res)
        my_bar.progress((i + 1) / total_stocks, text=f"Scanning {t.replace('.NS', '')} ({i+1}/{total_stocks})")
        
    my_bar.empty() 
                
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
        st.warning("No valid data could be retrieved.")
