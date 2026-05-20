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
    
    # 1. BATCH DOWNLOAD (Anti-Blocker Engine)
    with st.spinner("Downloading entire Nifty 200 data at once... (Bypassing blocks)"):
        data = yf.download(ticker_list, period="1y", group_by='ticker', threads=True, show_errors=False)
        
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
