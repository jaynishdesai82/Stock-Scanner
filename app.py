import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
import io
import os
import warnings
warnings.filterwarnings('ignore')

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide", page_icon="🏆")
st.title("🏆 Jaynish Trading Terminal")
st.write("Quantitative momentum engine and real-time paper execution ledger.")

# --- SILENT AUTO-BACKUP DIRECTORY SETUP ---
BACKUP_DIR = "Auto_Backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# --- INITIALIZE PORTFOLIO DATABASE ---
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame(columns=['Ticker', 'Type', 'Entry Price', 'Quantity', 'Stop Loss', 'Target'])

def tick(val):
    return float(round(float(val) * 20) / 20)

# --- BACKUP LISTS ---
FALLBACK_NIFTY_50 = "ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, BAJFINANCE, BAJAJFINSV, BPCL, BHARTIARTL, BRITANNIA, CIPLA, COALINDIA, DIVISLAB, DRREDDY, EICHERMOT, GRASIM, HCLTECH, HDFCBANK, HDFCLIFE, HEROMOTOCO, HINDALCO, HINDUNILVR, ICICIBANK, INDUSINDBK, INFY, ITC, JSWSTEEL, KOTAKBANK, LT, LTIM, M&M, MARUTI, NESTLEIND, NTPC, ONGC, POWERGRID, RELIANCE, SBILIFE, SBIN, SHRIRAMFIN, SUNPHARMA, TATACONSUM, TATAMOTORS, TATASTEEL, TCS, TECHM, TITAN, ULTRACEMCO, WIPRO"
FALLBACK_NIFTY_100 = FALLBACK_NIFTY_50 + ", ABB, AMBUJACEM, ATGL, AWL, BAJAJHLDNG, BANKBARODA, BEL, BHARATFORG, BHEL, BOSCHLTD, CANBK, CGPOWER, CHOLAMFIN, COCHINSHIP, COLPAL, DABUR, DIXON, DLF, DMART, GAIL, GODREJCP, GODREJPROP, HAL, HAVELLS, ICICIGI, ICICIPRULI, IGL, INDHOTEL, IRFC, JIOFIN, LUPIN, MARICO, MUTHOOTFIN, NAUKRI, NHPC, PIDILITIND, PIIND, PFC, RECLTD, RVNL, SCHAEFFLER, SHREECEM, SIEMENS, SRF, TORNTPHARM, TRENT, TVSMOTOR, UBL, VEDL, ZOMATO"
FALLBACK_NIFTY_200 = FALLBACK_NIFTY_100 + ", ABCAPITAL, ABFRL, ACC, ALKEM, APARINDS, ASHOKLEY, ASTRAL, AUBANK, AUROPHARMA, BALKRISIND, BANDHANBNK, BANKINDIA, BATAINDIA, BDL, BERGEPAINT, BIOCON, BSE, CDSL, CENTURYTEX, CUB, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DALBHARAT, DEEPAKNITR, DELHIVERY, DEVYANI, ESCORTS, EXIDEIND, FACT, FEDERALBNK, FORTIS, GLAND, GLENMARK, GMRINFRA, GUJGASLTD, HINDCOPPER, HINDPETRO, IDBI, IDFCFIRSTB, INDIANB, IPCALAB, IRCTC, JINDALSTEL, JSWENERGY, JUBLFOOD, KALYANKJIL, KANSAINER, KPITTECH, L&TFH, LAURUSLABS, LICHSGFIN, LICI, LODHA, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MOTILALOFS, MOTHERSON, MPHASIS, MRF, NATCOPHARM, NATIONALUM, NAVINFLUOR, NLCINDIA, NMDC, NYKAA, OBERREALTY, OFSS, OIL, PAGEIND, PATANJALI, PEL, PERSISTENT, PETRONET, PNB, POLYCAB, POONAWALLA, PRESTIGE, RADICO, RBLBANK, SAIL, SBICARD, SJVN, SKFINDIA, SOBHA, SOLARINDS, SONACOMS, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATAELXSI, TATAPOWER, TATATECH, TIINDIA, TORNTPOWER, TRIDENT, UCOBANK, UNIONBANK, VBL, VOLTAS, YESBANK"

@st.cache_data(ttl=86400) 
def fetch_nse_list(index_name):
    urls = {
        "Nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "Nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
        "Nifty 200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"
    }
    if index_name not in urls: return FALLBACK_NIFTY_200
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(urls[index_name], headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            return ", ".join(df['Symbol'].tolist())
        else: raise Exception("Blocked")
    except Exception:
        return FALLBACK_NIFTY_200

# --- UI NAVIGATION ---
tab_scanner, tab_portfolio, tab_tutorial, tab_options = st.tabs(["🎯 Live Market Scanner", "💼 Active Ledger", "📖 Logic Guide", "📈 Nifty Options Desk"])

# --- SIDEBAR ---
st.sidebar.header("⚙️ Scanner Settings")
app_mode = st.sidebar.radio("Scanner Engine:", ["📊 Base Version", "🔥 Pro Version (Sniper)"])
index_choice = st.sidebar.selectbox("Market Index:", ["Nifty 50", "Nifty 100", "Nifty 200", "Custom List"])

if index_choice == "Custom List":
    user_stocks = st.sidebar.text_area("Watchlist:", "RELIANCE, TCS, INFY", height=150)
    ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]
else:
    raw_stocks = fetch_nse_list(index_choice)
    ticker_list = [f"{s.strip().upper()}.NS" for s in raw_stocks.split(",") if s.strip()]

volume_multiplier = st.sidebar.slider("RVOL Threshold", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss %", 3.0, 8.0, 5.0, 0.5)
refresh_choice = st.sidebar.selectbox("Refresh Interval:", ["Off", "1 Minute", "2 Minutes", "5 Minutes"])
sleep_time = {"Off": 0, "1 Minute": 60, "2 Minutes": 120, "5 Minutes": 300}[refresh_choice]

# ================= TAB 1: SCANNER =================
with tab_scanner:
    results = []
    with st.spinner("Analyzing market momentum..."):
        data = yf.download(ticker_list + ["^NSEI"], period="1y", group_by='ticker', threads=False, progress=False)

    for t in ticker_list:
        try:
            df = data[t].dropna()
            if df.empty or len(df) < 200: continue
            
            df['50_SMA'] = df['Close'].rolling(window=50).mean()
            df['20_Vol_SMA'] = df['Volume'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            
            trend_ok = (current_price > float(latest['50_SMA']))
            volume_ok = float(latest['Volume']) > (float(latest['20_Vol_SMA']) * volume_multiplier)
            signal = "🚀 BUY SETUP" if (trend_ok and volume_ok) else "⏳ HOLD"
            
            results.append({
                "Ticker": t.replace(".NS", ""), "Signal": signal, 
                "Price (₹)": tick(current_price), "RVOL": round(float(latest['Volume']) / float(latest['20_Vol_SMA']), 2)
            })
        except: continue
        
    if results:
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        # Execution Deck
        buy_signals = df_results[df_results['Signal'].str.contains("BUY")]
        if not buy_signals.empty:
            sel = st.selectbox("Select Ticker to Execute:", buy_signals['Ticker'].tolist())
            if st.button("📈 Execute Paper Trade"):
                st.session_state['portfolio'] = pd.concat([st.session_state['portfolio'], pd.DataFrame([{'Ticker': sel, 'Entry Price': buy_signals[buy_signals['Ticker']==sel]['Price (₹)'].values[0], 'Quantity': 100}])], ignore_index=True)
                st.success("Trade added!")

# ================= TAB 2: LEDGER =================
with tab_portfolio:
    st.header("💼 Active Ledger")
    st.dataframe(st.session_state['portfolio'], use_container_width=True)

# ================= TAB 3: GUIDE =================
with tab_tutorial:
    st.header("📖 Logic Guide")
    st.write("Quantitative momentum engine.")

# ================= TAB 4: OPTIONS DESK =================
with tab_options:
    st.header("📈 Nifty Options Desk")
    col1, col2 = st.columns(2)
    with col1:
        nifty = yf.download("^NSEI", period="1d", progress=False)
        st.metric("Nifty Spot", f"₹{float(nifty['Close'].iloc[-1]):,.2f}")
    with col2:
        entry = st.number_input("Option Premium:", min_value=0.0)
        if entry > 0: st.write(f"Target: ₹{entry * 2:,.2f}")

# --- REFRESH ---
if sleep_time > 0:
    time.sleep(sleep_time)
    st.rerun()
