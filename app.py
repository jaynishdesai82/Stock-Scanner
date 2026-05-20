import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
import io
import warnings
warnings.filterwarnings('ignore')

# --- OFFICIAL BRANDING ---
st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide")

st.title("🏆 Jaynish Multi-Scanner")
st.write("Real-time automated dashboard tracking institutional momentum setups.")

# --- NSE TICK SIZE ROUNDING (0.05) ---
def tick(val):
    """Rounds any number to the nearest 0.05 and returns it strictly with 2 decimal places."""
    return f"{round(float(val) * 20) / 20:.2f}"

# --- BACKUP FALLBACK LISTS ---
FALLBACK_NIFTY_50 = "ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, BAJFINANCE, BAJAJFINSV, BPCL, BHARTIARTL, BRITANNIA, CIPLA, COALINDIA, DIVISLAB, DRREDDY, EICHERMOT, GRASIM, HCLTECH, HDFCBANK, HDFCLIFE, HEROMOTOCO, HINDALCO, HINDUNILVR, ICICIBANK, INDUSINDBK, INFY, ITC, JSWSTEEL, KOTAKBANK, LT, LTIM, M&M, MARUTI, NESTLEIND, NTPC, ONGC, POWERGRID, RELIANCE, SBILIFE, SBIN, SHRIRAMFIN, SUNPHARMA, TATACONSUM, TATAMOTORS, TATASTEEL, TCS, TECHM, TITAN, ULTRACEMCO, WIPRO"

FALLBACK_NIFTY_100 = FALLBACK_NIFTY_50 + ", ABB, AMBUJACEM, ATGL, AWL, BAJAJHLDNG, BANKBARODA, BEL, BHARATFORG, BHEL, BOSCHLTD, CANBK, CGPOWER, CHOLAMFIN, COCHINSHIP, COLPAL, DABUR, DIXON, DLF, DMART, GAIL, GODREJCP, GODREJPROP, HAL, HAVELLS, ICICIGI, ICICIPRULI, IGL, INDHOTEL, IRFC, JIOFIN, LUPIN, MARICO, MUTHOOTFIN, NAUKRI, NHPC, PIDILITIND, PIIND, PFC, RECLTD, RVNL, SCHAEFFLER, SHREECEM, SIEMENS, SRF, TORNTPHARM, TRENT, TVSMOTOR, UBL, VEDL, ZOMATO"

FALLBACK_NIFTY_200 = FALLBACK_NIFTY_100 + ", ABCAPITAL, ABFRL, ACC, ALKEM, APARINDS, ASHOKLEY, ASTRAL, AUBANK, AUROPHARMA, BALKRISIND, BANDHANBNK, BANKINDIA, BATAINDIA, BDL, BERGEPAINT, BIOCON, BSE, CDSL, CENTURYTEX, CUB, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DALBHARAT, DEEPAKNITR, DELHIVERY, DEVYANI, ESCORTS, EXIDEIND, FACT, FEDERALBNK, FORTIS, GLAND, GLENMARK, GMRINFRA, GUJGASLTD, HINDCOPPER, HINDPETRO, IDBI, IDFCFIRSTB, INDIANB, IPCALAB, IRCTC, JINDALSTEL, JSWENERGY, JUBLFOOD, KALYANKJIL, KANSAINER, KPITTECH, L&TFH, LAURUSLABS, LICHSGFIN, LICI, LODHA, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MOTILALOFS, MOTHERSON, MPHASIS, MRF, NATCOPHARM, NATIONALUM, NAVINFLUOR, NLCINDIA, NMDC, NYKAA, OBERREALTY, OFSS, OIL, PAGEIND, PATANJALI, PEL, PERSISTENT, PETRONET, PNB, POLYCAB, POONAWALLA, PRESTIGE, RADICO, RBLBANK, SAIL, SBICARD, SJVN, SKFINDIA, SOBHA, SOLARINDS, SONACOMS, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATAELXSI, TATAPOWER, TATATECH, TIINDIA, TORNTPOWER, TRIDENT, UCOBANK, UNIONBANK, VBL, VOLTAS, YESBANK"

# --- LIVE NSE AUTO-UPDATER ---
@st.cache_data(ttl=86400) 
def fetch_nse_list(index_name):
    urls = {
        "Nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "Nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
        "Nifty 200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"
    }
    if index_name not in urls:
        return "RELIANCE, TCS, INFY"
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(urls[index_name], headers=headers, timeout=5)
        df = pd.read_csv(io.StringIO(response.text))
        return ", ".join(df['Symbol'].tolist())
    except Exception:
        if index_name == "Nifty 50": return FALLBACK_NIFTY_50
        if index_name == "Nifty 100": return FALLBACK_NIFTY_100
        if index_name == "Nifty 200": return FALLBACK_NIFTY_200
        return "RELIANCE, TCS, INFY"

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Scanner Settings")

app_mode = st.sidebar.radio(
    "Select Scanner Mode:",
    ["📊 Basic Version (Trend & Volume)", "🔥 Pro Version (Sniper Metrics)"]
)
st.sidebar.markdown("---")

index_choice = st.sidebar.selectbox(
    "Select Market Index:",
    ["Nifty 50", "Nifty 100", "Nifty 200", "Custom List"]
)

if index_choice == "Custom List":
    default_text = "RELIANCE, TCS, INFY" 
else:
    default_text = fetch_nse_list(index_choice)

user_stocks = st.sidebar.text_area("Watchlist (Separate with commas):", default_text, height=150)

st.sidebar.markdown("---")
volume_multiplier = st.sidebar.slider("Volume Breakout Multiplier (x SMA)", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss Risk %", 3.0, 8.0, 5.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Auto-Pilot")

refresh_choice = st.sidebar.selectbox(
    "Auto-Refresh Interval:",
    ["Off", "1 Minute", "2 Minutes", "5 Minutes", "10 Minutes"]
)

refresh_dict = {
    "Off": 0,
    "1 Minute": 60,
    "2 Minutes": 120,
    "5 Minutes": 300,
    "10 Minutes": 600
}
sleep_time = refresh_dict[refresh_choice]

ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]

# --- DASHBOARD ENGINE ---
results = []
skipped_count = 0

with st.spinner(f"Downloading {index_choice} live data..."):
    data = yf.download(ticker_list, period="1y", group_by='ticker', threads=False, progress=False)
    
progress_text = f"Analyzing setups using {app_mode.split(' ')[1]}..."
my_bar = st.progress(0, text=progress_text)

total_stocks = len(ticker_list)

# ANALYSIS LOOP
for i, t in enumerate(ticker_list):
    try:
        if len(ticker_list) == 1:
            df = data.dropna()
        else:
            df = data[t].dropna()
            
        # The safety rule: Skip stocks without 200 days of history
        if df.empty or len(df) < 200:
            skipped_count += 1
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
                
            show_levels = "SELL" not in signal
                
            results.append({
                "Ticker": t.replace(".NS", ""),
                "Signal": signal,
                "Price (₹)": tick(current_price),
                "Volume": f"{int(current_volume):,}",
                "RSI": round(rsi, 1),
                "MACD": "UP 📈" if macd_bullish else "DOWN 📉",
                "Vol Mult": round(current_volume / vol_sma, 2),
                "50 SMA (₹)": tick(sma_50),
                "Stop Loss": tick(sl_price) if show_levels else "---",
                "Target": tick(target_3r) if show_levels else "---"
            })
            
        # BASIC MODE
        else:
            if trend_ok and volume_ok and price_ok:
                signal = "🚀 BUY SETUP"
            elif current_price < sma_50:
                signal = "🛑 CASH/SELL"
            else:
                signal = "⏳ HOLD"
                
            show_levels = "SELL" not in signal
                
            results.append({
                "Ticker": t.replace(".NS", ""),
                "Signal": signal,
                "Price (₹)": tick(current_price),
                "Volume": f"{int(current_volume):,}",
                "Vol Mult": round(current_volume / vol_sma, 2),
                "50 SMA (₹)": tick(sma_50),
                "200 SMA (₹)": tick(sma_200),
                "Stop Loss": tick(sl_price) if show_levels else "---",
                "Target": tick(target_3r) if show_levels else "---"
            })

    except Exception as e:
        skipped_count += 1
        continue
        
    my_bar.progress((i + 1) / total_stocks, text=f"Analyzing {t.replace('.NS', '')} ({i+1}/{total_stocks})")
    
my_bar.empty() 
            
# DISPLAY TABLE AND SUMMARY
if results:
    df_results = pd.DataFrame(results)
    
    # --- THIS FIXES THE ZERO INDEX ISSUE ---
    df_results.index = df_results.index + 1 
    
    def color_signals(val):
        if "SNIPER BUY" in val: return 'background-color: #8e44ad; color: white; font-weight: bold;'
        if "BUY" in val: return 'background-color: #2ecc71; color: white; font-weight: bold;'
        if "CASH" in val: return 'background-color: #e74c3c; color: white;'
        return 'background-color: #f1c40f; color: black;'
        
    styled_df = df_results.style.map(color_signals, subset=['Signal'])
    st.dataframe(styled_df, use_container_width=True, height=500)
    
    # Let the user know if any stocks were safely skipped
    if skipped_count > 0:
        st.caption(f"*(Note: {skipped_count} stocks were excluded from this scan because they are recent listings and do not have enough history to calculate a 200-Day Moving Average).*")
    
    st.markdown("---")
    st.subheader("📋 Quick Action Summary")
    
    sniper_stocks = df_results[df_results['Signal'] == "🔥 SNIPER BUY"]['Ticker'].tolist()
    base_buy_stocks = df_results[df_results['Signal'].isin(["🚀 BASE BUY", "🚀 BUY SETUP"])]['Ticker'].tolist()
    sell_stocks = df_results[df_results['Signal'] == "🛑 CASH/SELL"]['Ticker'].tolist()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**🔥 Sniper Setups:**\n\n{', '.join(sniper_stocks) if sniper_stocks else 'None right now'}")
    with col2:
        st.success(f"**🚀 Base Breakouts:**\n\n{', '.join(base_buy_stocks) if base_buy_stocks else 'None right now'}")
    with col3:
        st.error(f"**🛑 Sell / Weakness:**\n\n{', '.join(sell_stocks) if sell_stocks else 'None right now'}")

else:
    st.error("Could not fetch data. The market might be closed or API is temporarily down.")

# --- AUTO REFRESH LOOP ---
if sleep_time > 0:
    st.sidebar.success(f"⏱️ Auto-Pilot Active: Refreshing in {sleep_time} seconds.")
    time.sleep(sleep_time)
    st.rerun()
