import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
import io
import os
import warnings
from nsepython import nse_quote_ltp
warnings.filterwarnings('ignore')

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide", page_icon="🏆")
st.title("🏆 Jaynish Trading Terminal")
st.write("Quantitative momentum engine and real-time paper execution ledger.")

# --- FUNDAMENTAL FETCH ENGINE ---
def get_fundamental_data(symbol):
    try:
        # Fetches official NSE data
        data = nse_quote_ltp(symbol)
        return data
    except Exception as e:
        return f"Error fetching: {e}"

# --- SILENT AUTO-BACKUP DIRECTORY SETUP ---
BACKUP_DIR = "Auto_Backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# --- INITIALIZE PORTFOLIO DATABASE ---
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame(columns=['Ticker', 'Type', 'Entry Price', 'Quantity', 'Stop Loss', 'Target'])

def tick(val):
    return float(round(float(val) * 20) / 20)

# --- THE MASSIVE BACKUP LISTS ---
FALLBACK_NIFTY_50 = "ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, BAJFINANCE, BAJAJFINSV, BPCL, BHARTIARTL, BRITANNIA, CIPLA, COALINDIA, DIVISLAB, DRREDDY, EICHERMOT, GRASIM, HCLTECH, HDFCBANK, HDFCLIFE, HEROMOTOCO, HINDALCO, HINDUNILVR, ICICIBANK, INDUSINDBK, INFY, ITC, JSWSTEEL, KOTAKBANK, LT, LTIM, M&M, MARUTI, NESTLEIND, NTPC, ONGC, POWERGRID, RELIANCE, SBILIFE, SBIN, SHRIRAMFIN, SUNPHARMA, TATACONSUM, TATAMOTORS, TATASTEEL, TCS, TECHM, TITAN, ULTRACEMCO, WIPRO"
FALLBACK_NIFTY_100 = FALLBACK_NIFTY_50 + ", ABB, AMBUJACEM, ATGL, AWL, BAJAJHLDNG, BANKBARODA, BEL, BHARATFORG, BHEL, BOSCHLTD, CANBK, CGPOWER, CHOLAMFIN, COCHINSHIP, COLPAL, DABUR, DIXON, DLF, DMART, GAIL, GODREJCP, GODREJPROP, HAL, HAVELLS, ICICIGI, ICICIPRULI, IGL, INDHOTEL, IRFC, JIOFIN, LUPIN, MARICO, MUTHOOTFIN, NAUKRI, NHPC, PIDILITIND, PIIND, PFC, RECLTD, RVNL, SCHAEFFLER, SHREECEM, SIEMENS, SRF, TORNTPHARM, TRENT, TVSMOTOR, UBL, VEDL, ZOMATO"
FALLBACK_NIFTY_200 = FALLBACK_NIFTY_100 + ", ABCAPITAL, ABFRL, ACC, ALKEM, APARINDS, ASHOKLEY, ASTRAL, AUBANK, AUROPHARMA, BALKRISIND, BANDHANBNK, BANKINDIA, BATAINDIA, BDL, BERGEPAINT, BIOCON, BSE, CDSL, CENTURYTEX, CUB, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DALBHARAT, DEEPAKNITR, DELHIVERY, DEVYANI, ESCORTS, EXIDEIND, FACT, FEDERALBNK, FORTIS, GLAND, GLENMARK, GMRINFRA, GUJGASLTD, HINDCOPPER, HINDPETRO, IDBI, IDFCFIRSTB, INDIANB, IPCALAB, IRCTC, JINDALSTEL, JSWENERGY, JUBLFOOD, KALYANKJIL, KANSAINER, KPITTECH, L&TFH, LAURUSLABS, LICHSGFIN, LICI, LODHA, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MOTILALOFS, MOTHERSON, MPHASIS, MRF, NATCOPHARM, NATIONALUM, NAVINFLUOR, NLCINDIA, NMDC, NYKAA, OBERREALTY, OFSS, OIL, PAGEIND, PATANJALI, PEL, PERSISTENT, PETRONET, PNB, POLYCAB, POONAWALLA, PRESTIGE, RADICO, RBLBANK, SAIL, SBICARD, SJVN, SKFINDIA, SOBHA, SOLARINDS, SONACOMS, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATAELXSI, TATAPOWER, TATATECH, TIINDIA, TORNTPOWER, TRIDENT, UCOBANK, UNIONBANK, VBL, VOLTAS, YESBANK"

@st.cache_data(ttl=86400) 
def fetch_nse_list(index_name):
    urls = {
        "Nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "Nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
        "Nifty 200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv",
    }
    if index_name not in urls:
        return FALLBACK_NIFTY_200
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(urls[index_name], headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            return ", ".join(df['Symbol'].tolist())
        else:
            raise Exception("Blocked")
    except Exception:
        if index_name == "Nifty 50": return FALLBACK_NIFTY_50
        if index_name == "Nifty 100": return FALLBACK_NIFTY_100
        return FALLBACK_NIFTY_200

# --- UI NAVIGATION ---
tab_scanner, tab_portfolio, tab_tutorial = st.tabs(["🎯 Live Market Scanner", "💼 Active Ledger", "📖 Logic Guide"])

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
refresh_dict = {"Off": 0, "1 Minute": 60, "2 Minutes": 120}
sleep_time = refresh_dict[st.sidebar.selectbox("Refresh:", ["Off", "1 Minute", "2 Minutes"])]

# ================= TAB 1: SCANNER =================
with tab_scanner:
    results = []
    download_list = ticker_list + ["^NSEI"]
    with st.spinner("Syncing Market Matrix..."):
        data = yf.download(download_list, period="1y", group_by='ticker', threads=False, progress=False)

    for t in ticker_list:
        try:
            df = data[t].dropna()
            if df.empty or len(df) < 200: continue
            
            df['50_SMA'] = df['Close'].rolling(window=50).mean()
            df['200_SMA'] = df['Close'].rolling(window=200).mean()
            df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            
            # Signals (Simplified for stability)
            trend_ok = (current_price > float(latest['50_SMA']))
            volume_ok = float(latest['Volume']) > (float(latest['Vol_SMA']) * volume_multiplier)
            signal = "🚀 BUY SETUP" if (trend_ok and volume_ok) else "⏳ HOLD"
            
            # Intraday Check
            intraday_status = "---"
            if "BUY" in signal:
                time.sleep(1.5) # Anti-block
                intra = yf.download(t, period="5d", interval="15m", progress=False)
                if not intra.empty:
                    intraday_status = "🔥 ACTIVE" if intra['Close'].iloc[-1] > intra['Close'].ewm(span=20).mean().iloc[-1] else "💤 FADING"

            results.append({
                "Ticker": t.replace(".NS", ""),
                "Signal": signal,
                "Live 15m Trend": intraday_status,
                "Price (₹)": tick(current_price),
                "Volume": int(latest['Volume']),
                "RVOL": round(float(latest['Volume']) / float(latest['Vol_SMA']), 2)
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
                st.success("Trade added to Ledger!")

# ================= TAB 2: LEDGER =================
with tab_portfolio:
    st.header("💼 Active Ledger")
    st.subheader("🔍 Fundamental Fetcher")
    test_symbol = st.text_input("Test NSE Symbol (e.g., RELIANCE):").upper()
    if st.button("Fetch Fundamentals"):
        st.write(get_fundamental_data(test_symbol))
    
    st.dataframe(st.session_state['portfolio'], use_container_width=True)

# --- REFRESH ---
if sleep_time > 0:
    time.sleep(sleep_time)
    st.rerun()
