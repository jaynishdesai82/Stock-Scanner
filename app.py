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

# --- BACKUP LISTS (Shortened for brevity - replace with full lists if needed) ---
FALLBACK_NIFTY_200 = "RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, TATAMOTORS, SBIN, BHARTIARTL" 

@st.cache_data(ttl=86400) 
def fetch_nse_list(index_name):
    urls = {
        "Nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "Nifty Next 50": "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv",
        "Nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
        "Nifty Midcap 100": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap100list.csv",
        "Nifty 200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv",
        "Nifty 500": "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    }
    if index_name not in urls:
        return FALLBACK_NIFTY_200
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/csv,text/html,application/xhtml+xml',
            'Referer': 'https://www.niftyindices.com/'
        }
        response = requests.get(urls[index_name], headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            return ", ".join(df['Symbol'].tolist())
        else:
            raise Exception("Blocked by NSE")
    except Exception:
        return FALLBACK_NIFTY_200

# --- UI NAVIGATION CONFIGURATION ---
tab_scanner, tab_portfolio, tab_tutorial = st.tabs(["🎯 Live Market Scanner", "💼 Active Ledger", "📖 Logic Guide"])

# --- SIDEBAR GLOBAL SYSTEM FILTERS ---
st.sidebar.header("⚙️ Scanner Settings")
app_mode = st.sidebar.radio("Scanner Engine:", ["📊 Base Version", "🔥 Pro Version (Sniper)"])
st.sidebar.markdown("---")
index_choice = st.sidebar.selectbox("Market Index:", ["Nifty 50", "Nifty Next 50", "Nifty 100", "Nifty Midcap 100", "Nifty 200", "Nifty 500", "Custom List"])

if index_choice == "Custom List":
    user_stocks = st.sidebar.text_area("Watchlist (Separate with commas):", "RELIANCE, TCS, INFY", height=150)
    ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]
else:
    raw_stocks = fetch_nse_list(index_choice)
    ticker_list = [f"{s.strip().upper()}.NS" for s in raw_stocks.split(",") if s.strip()]

st.sidebar.markdown("---")
volume_multiplier = st.sidebar.slider("RVOL Threshold", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss %", 3.0, 8.0, 5.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Auto-Pilot")
refresh_choice = st.sidebar.selectbox("Refresh Interval:", ["Off", "1 Minute", "2 Minutes", "5 Minutes", "10 Minutes"])
refresh_dict = {"Off": 0, "1 Minute": 60, "2 Minutes": 120, "5 Minutes": 300, "10 Minutes": 600}
sleep_time = refresh_dict[refresh_choice]

# =====================================================================
# TAB 1: THE SCANNER ENGINE & EXECUTION DECK
# =====================================================================
with tab_scanner:
    results = []
    skipped_count = 0
    download_list = ticker_list.copy()
    if "^NSEI" not in download_list:
        download_list.append("^NSEI")

    with st.spinner(f"Synchronizing {index_choice} pricing matrix..."):
        # BATCH DOWNLOAD (threads=False to bypass cloud server blocking)
        data = yf.download(download_list, period="1y", group_by='ticker', threads=False, progress=False)

    try:
        nifty_df = data["^NSEI"].dropna()
        nifty_6m_old = nifty_df['Close'].iloc[-126] if len(nifty_df) >= 126 else nifty_df['Close'].iloc[0]
        nifty_benchmark_ret = (float(nifty_df['Close'].iloc[-1]) - float(nifty_6m_old)) / float(nifty_6m_old)
    except Exception:
        nifty_benchmark_ret = 0.10 

    my_bar = st.progress(0, text=f"Analyzing technical setups...")
    total_stocks = len(ticker_list)

    for i, t in enumerate(ticker_list):
        try:
            if len(ticker_list) == 1 and "^NSEI" not in ticker_list:
                df = data.dropna()
            else:
                df = data[t].dropna()
                
            if df.empty or len(df) < 200:
                skipped_count += 1
                continue
            
            df['50_SMA'] = df['Close'].rolling(window=50).mean()
            df['200_SMA'] = df['Close'].rolling(window=200).mean()
            df['20_Vol_SMA'] = df['Volume'].rolling(window=20).mean()
            
            df['BB_Mid'] = df['Close'].rolling(window=20).mean()
            df['BB_Std'] = df['Close'].rolling(window=20).std()
            df['BB_Width'] = (df['BB_Std'] * 4) / df['BB_Mid']
            df['BB_Width_SMA'] = df['BB_Width'].rolling(window=100).mean()
            
            latest = df.iloc[-1]
            prev_close = df.iloc[-2]['Close']
            
            current_price = float(latest['Close'])
            current_volume = float(latest['Volume'])
            sma_50 = float(latest['50_SMA'])
            sma_200 = float(latest['200_SMA'])
            vol_sma = float(latest['20_Vol_SMA'])
            
            current_bw = float(latest['BB_Width'])
            avg_bw = float(latest['BB_Width_SMA'])
            is_squeezing = current_bw < (avg_bw * 0.82)
            vol_status = "💥 SQUEEZE" if is_squeezing else "Normal"
            
            stock_6m_old = df['Close'].iloc[-126] if len(df) >= 126 else df['Close'].iloc[0]
            stock_ret = (current_price - float(stock_6m_old)) / float(stock_6m_old)
            relative_strength_ratio = round((1 + stock_ret) / (1 + nifty_benchmark_ret), 2)
            
            high_52w = float(df['High'].max())
            pct_from_52w = float(((current_price - high_52w) / high_52w) * 100)
            
            trend_ok = (current_price > sma_50) and (sma_50 > sma_200)
            volume_ok = current_volume > (vol_sma * volume_multiplier)
            price_ok = current_price > float(prev_close)
            
            sl_price = current_price * (1 - (risk_pct / 100))
            target_3r = current_price * (1 + (risk_pct * 3 / 100))
            
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
            else:
                if trend_ok and volume_ok and price_ok:
                    signal = "🚀 BUY SETUP"
                elif current_price < sma_50:
                    signal = "🛑 CASH/SELL"
                else:
                    signal = "⏳ HOLD"
            
            show_levels = "SELL" not in signal
            
            latest_news = None
            intraday_status = "---"
            smart_vwap = "---"
            
            if "BUY" in signal:
                try:
                    stock_info = yf.Ticker(t)
                    news_list = stock_info.news
                    if news_list and len(news_list) > 0:
                        title = news_list[0].get('title', 'News Link')
                        link = news_list[0].get('link', '#')
                        latest_news = f"[{title[:40]}...]({link})" 
                except Exception:
                    latest_news = "News unavailable"
                    
                try:
                    # THE FIX 1: Add a 1.5-second stealth pause to bypass Yahoo's bot-blocker
                    time.sleep(1.5) 
                    
                    intra_data = yf.download(t, period="5d", interval="15m", progress=False)
                    
                    if intra_data is not None and not intra_data.empty:
                        # THE FIX 2: Flatten the table structure if yfinance uses MultiIndex
                        if isinstance(intra_data.columns, pd.MultiIndex):
                            intra_data.columns = intra_data.columns.droplevel(1)
                            
                        # 15m Trend Logic
                        intra_data['20_EMA'] = intra_data['Close'].ewm(span=20, adjust=False).mean()
                        last_close = float(intra_data['Close'].iloc[-1])
                        last_ema = float(intra_data['20_EMA'].iloc[-1])
                        
                        if last_close > last_ema:
                            intraday_status = "🔥 ACTIVE"
                        else:
                            intraday_status = "💤 FADING"
                            
                        # THE FIX 3: Bulletproof date filtering for VWAP
                        today_str = str(intra_data.index[-1].date())
                        today_data = intra_data.loc[today_str].copy()
                        
                        if not today_data.empty:
                            today_data['Typical_Price'] = (today_data['High'] + today_data['Low'] + today_data['Close']) / 3
                            today_data['TP_V'] = today_data['Typical_Price'] * today_data['Volume']
                            vol_sum = today_data['Volume'].sum()
                            
                            if vol_sum > 0:
                                final_vwap = today_data['TP_V'].sum() / vol_sum
                                if last_close >= final_vwap:
                                    smart_vwap = "🟢 BUYING"
                                else:
                                    smart_vwap = "🔴 SELLING"
                except Exception as e:
                    intraday_status = "API Blocked"
                    smart_vwap = "API Blocked"

            row_data = {
                "Ticker": t.replace(".NS", ""),
                "Signal": signal,
                "Live 15m Trend": intraday_status,
                "Smart Money (VWAP)": smart_vwap,
                "Price (₹)": tick(current_price),
                "% from 52W High": round(pct_from_52w, 1),
                "Volume": int(current_volume),
                "RVOL": round(current_volume / vol_sma, 2),
                "Market RS": relative_strength_ratio,
                "Volatility Profile": vol_status
            }
            
            if "Pro Version" in app_mode:
                row_data.update({
                    "RSI": round(rsi, 1),
                    "MACD": "UP 📈" if macd_bullish else "DOWN 📉",
                })
                
            row_data.update({
                "50 SMA (₹)": tick(sma_50),
                "Stop Loss (₹)": tick(sl_price) if show_levels else None,
                "Target (₹)": tick(target_3r) if show_levels else None,
                "Latest Catalyst": latest_news
            })
            
            results.append(row_data)

        except Exception as e:
            skipped_count += 1
            continue
            
        my_bar.progress((i + 1) / total_stocks, text=f"Analyzing {t.replace('.NS', '')} ({i+1}/{total_stocks})")
        
    my_bar.empty() 
                
    if results:
        df_results = pd.DataFrame(results)
        
        # --- SILENT AUTO-BACKUP EXECUTION ---
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(BACKUP_DIR, f"Scan_Log_{timestamp}.csv")
            df_results.to_csv(backup_path, index=False)
        except Exception as e:
            pass # Fails silently so it never interrupts the app
        
        def color_signals(val):
            if "SNIPER BUY" in val: return 'background-color: #8e44ad; color: white; font-weight: bold;'
            if "BUY" in val: return 'background-color: #2ecc71; color: white; font-weight: bold;'
            if "CASH" in val: return 'background-color: #e74c3c; color: white;'
            return 'background-color: #f1c40f; color: black;'
            
        def color_highs(val):
            if pd.isna(val): return ''
            try:
                num = float(val)
                if num >= -5.0: return 'color: #2ecc71; font-weight: bold;' 
                if num <= -30.0: return 'color: #e74c3c;' 
                return ''
            except: return ''

        def color_squeeze(val):
            if
