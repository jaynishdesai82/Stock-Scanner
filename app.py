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

# --- STEALTH SCRAPER LIVE OPTIONS CONNECTION TEST ---
def test_live_option_chain():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        session = requests.Session()
        # Step 1: Visit homepage to get cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        
        # Step 2: Request the Nifty Option Chain
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return f"✅ SUCCESS! Fetched {len(data['records']['data'])} Option Strikes."
        else:
            return f"❌ BLOCKED: NSE returned Status Code {response.status_code}"
    except Exception as e:
        return f"❌ ERROR: {e}"

# --- THE MASSIVE BACKUP LISTS ---
FALLBACK_NIFTY_50 = "ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, BAJFINANCE, BAJAJFINSV, BPCL, BHARTIARTL, BRITANNIA, CIPLA, COALINDIA, DIVISLAB, DRREDDY, EICHERMOT, GRASIM, HCLTECH, HDFCBANK, HDFCLIFE, HEROMOTOCO, HINDALCO, HINDUNILVR, ICICIBANK, INDUSINDBK, INFY, ITC, JSWSTEEL, KOTAKBANK, LT, LTIM, M&M, MARUTI, NESTLEIND, NTPC, ONGC, POWERGRID, RELIANCE, SBILIFE, SBIN, SHRIRAMFIN, SUNPHARMA, TATACONSUM, TATAMOTORS, TATASTEEL, TCS, TECHM, TITAN, ULTRACEMCO, WIPRO"
FALLBACK_NIFTY_100 = FALLBACK_NIFTY_50 + ", ABB, AMBUJACEM, ATGL, AWL, BAJAJHLDNG, BANKBARODA, BEL, BHARATFORG, BHEL, BOSCHLTD, CANBK, CGPOWER, CHOLAMFIN, COCHINSHIP, COLPAL, DABUR, DIXON, DLF, DMART, GAIL, GODREJCP, GODREJPROP, HAL, HAVELLS, ICICIGI, ICICIPRULI, IGL, INDHOTEL, IRFC, JIOFIN, LUPIN, MARICO, MUTHOOTFIN, NAUKRI, NHPC, PIDILITIND, PIIND, PFC, RECLTD, RVNL, SCHAEFFLER, SHREECEM, SIEMENS, SRF, TORNTPHARM, TRENT, TVSMOTOR, UBL, VEDL, ZOMATO"
FALLBACK_NIFTY_200 = FALLBACK_NIFTY_100 + ", ABCAPITAL, ABFRL, ACC, ALKEM, APARINDS, ASHOKLEY, ASTRAL, AUBANK, AUROPHARMA, BALKRISIND, BANDHANBNK, BANKINDIA, BATAINDIA, BDL, BERGEPAINT, BIOCON, BSE, CDSL, CENTURYTEX, CUB, CONCOR, COROMANDEL, CROMPTON, CUMMINSIND, CYIENT, DALBHARAT, DEEPAKNITR, DELHIVERY, DEVYANI, ESCORTS, EXIDEIND, FACT, FEDERALBNK, FORTIS, GLAND, GLENMARK, GMRINFRA, GUJGASLTD, HINDCOPPER, HINDPETRO, IDBI, IDFCFIRSTB, INDIANB, IPCALAB, IRCTC, JINDALSTEL, JSWENERGY, JUBLFOOD, KALYANKJIL, KANSAINER, KPITTECH, L&TFH, LAURUSLABS, LICHSGFIN, LICI, LODHA, MAHABANK, MANAPPURAM, MAZDOCK, MAXHEALTH, METROPOLIS, MOTILALOFS, MOTHERSON, MPHASIS, MRF, NATCOPHARM, NATIONALUM, NAVINFLUOR, NLCINDIA, NMDC, NYKAA, OBERREALTY, OFSS, OIL, PAGEIND, PATANJALI, PEL, PERSISTENT, PETRONET, PNB, POLYCAB, POONAWALLA, PRESTIGE, RADICO, RBLBANK, SAIL, SBICARD, SJVN, SKFINDIA, SOBHA, SOLARINDS, SONACOMS, SUNTV, SUPREMEIND, SUZLON, SYNGENE, TATACHEM, TATACOMM, TATAELXSI, TATAPOWER, TATATECH, TIINDIA, TORNTPOWER, TRIDENT, UCOBANK, UNIONBANK, VBL, VOLTAS, YESBANK"
FALLBACK_NIFTY_500 = FALLBACK_NIFTY_200 + ", 360ONE, 3MINDIA, AARTIDRUGS, AARTIIND, AAVAS, ABBOTINDIA, ADVENZYMES, AEGISCHEM, AFFLE, AJANTPHARM, AKZOINDIA, ALEMBICLTD, ALOKINDS, AMARAJABAT, AMBER, ANGELONE, ANURAS, APARINDS, APTUS, APLAPOLLO, ASANIFIN, ASTERDM, ASTRAZEN, ATUL, AVANTIFEED, BATAINDIA, BEML, BLUEDART, BLUESTARCO, BOMDYEING, BRIGADE, BSOFT, CAMPUS, CASTROLIND, CCL, CERA, CGCL, CHALET, CHAMBLFERT, CHEMPLASTS, CHENNPETRO, CAMS, CLEAN, COCHINSHIP, CRAFTSMAN, CREDITACC, CRISIL, CROMPTON, CSBBANK, CUB, CYIENT, DATAPATTNS, DEEPAKFERT, DELTACORP, DEVYANI, EIDPARRY, EIHOTEL, ENDURANCE, ENGINERSIN, EQUITASBNK, ERIS, ESCORTS, ETHER, EXIDEIND, FDC, FINCABLES, FINPIPE, FSL, GABRIEL, GARFIBRES, GEOMETRIC, GLAND, GLENMARK, GMDCLTD, GMMPFAUDLR, GODFRYPHLP, GODREJIND, GRANULES, GRAPHITE, GRINDWELL, GUJALKALI, GUJGASLTD, GNFC, GSFC, HAPPSTMNDS, HATHWAY, HEG, HFCL, HGS, HIKAL, HINDCOPPER, HINDUJAVEN, HINDZINC, HONAUT, HSCL, HUDCO, IBULHSGFIN, ICIL, IDFC, IFBIND, IGL, IIFL, INDIAMART, INDIANB, INDIGOPNTS, INDUSINDBK, INFY, INOXLEISUR, INTELLECT, IOB, IONEXCHANG, IRB, IRCON, ISEC, ISGEC, ITDC, ITDCEM, ITI, J&KBANK, JAGRAN, JAICORPLTD, JSWENERGY, JUBLFOOD, JUBLINGREA, JUBLPHARMA, JUSTDIAL, JYOTHYLAB, KAIT, KAJARIACER, KALPATPOWR, KALYANKJIL, KANSAINER, KAPSTON, KARURVYSYA, KEC, KEI, KIMS, KOTAKBANK, KPITTECH, KPRMILL, KRBL, KSB, LALPATHLAB, LATENTVIEW, LAURUSLABS, LAXMIMACH, LEMONTREE, LICHSGFIN, LICI, LINDEINDIA, LODHA, LUXIND, M&MFIN, MAHABANK, MAHLOG, MAHSCOOTER, MANAPPURAM, MARICO, MASFIN, MASTEK, MATRIMONY, MAXHEALTH, MAZDOCK, MEDPLUS, METROPOLIS, MGL, MINDAIND, MINDACORP, MOLDTKPAC, MOTILALOFS, MPF, MRF, MRPL, MSTC, MTARTECH, MUTHOOTFIN, NATCOPHARM, NATIONALUM, NAVINFLUOR, NAZARA, NCC, NEOGEN, NESCO, NETWORK18, NH, NILKAMAL, NLCINDIA, NMDC, NOCIL, NUVOCO, NYKAA, OBERREALTY, OFSS, OIL, OLECTRA, ORIENTELEC, PAGEIND, PATANJALI, PCBL, PEL, PERSISTENT, PETRONET, PFIZER, PHOENIXLTD, PIIND, PNBHOUSING, PNCINFRA, POLYCAB, POLYMED, POONAWALLA, POWERINDIA, PRAJIND, PRESTIGE, PRINCEPIPE, PRSMJOHNSN, PVRINOX, QUESS, RADICO, RAILTEL, RAIN, RAJESHEXPO, RALLIS, RAMCOCEM, RAMCOIND, RATNAMANI, RBLBANK, RECLTD, REDINGTON, RELAXO, RELIGARE, RESTAURANT, RITES, ROUTE, ROLEXRINGS, ROSSELLIND, RVNL, SAFARI, SAGCEM, SAIL, SANOFI, SAPPHIRE, SAREGAMA, SBICARD, SCHAEFFLER, SCI, SEQUENT, SFL, SHILPAMED, SHOOPERS, SHREECEM, SHRIRAMFIN, SHYAMMETL, SIEMENS, SIS, SJVN, SKFINDIA, SOBHA, SOLARINDS, SONACOMS, SOUTHBANK, SPARC, STARCEMENT, STARHEALTH, STLTECH, SUMICHEM, SUNDARMFIN, SUNDRMFAST, SUNTECK, SUPRAJIT, SUPREMEIND, SURYAROSNI, SUVENPHAR, SUZLON, SWANENERGY, SYMPHONY, SYNGENE, TATACHEM, TATACOMM, TATAELXSI, TATAINVEST, TATAMETALI, TATAPOWER, TATASTEEL, TATATECH, TCI, TCIEXP, TCNSBRANDS, TEJASNET, THERMAX, THOMASCOOK, TIMKEN, TITAGARH, TORNTPHARM, TORNTPOWER, TRENT, TRIDENT, TRITURBINE, TTKPRESTIG, TTML, TV18BRDCST, TVSMOTOR, UCOBANK, UJJIVANSFB, ULTRACEMCO, UNIONBANK, UNOMINDA, UTIAMC, VAKRANGEE, VALIANTORG, VBL, VEDL, VENKEYS, VESUVIUS, VGUARD, VINATIORG, VIPIND, VOLTAS, VRLLOG, VTL, WELCORP, WELENT, WELSPUNIND, WHIRLPOOL, WIPRO, WOCKPHARMA, YESBANK, ZEELEARN, ZEEL, ZENSARTECH, ZOMATO, ZYDUSLIFE, ZYDUSWELL"

# --- LIVE NSE AUTO-UPDATER WITH PROPER ROUTING FIX ---
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
        return "RELIANCE, TCS, INFY"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        if index_name == "Nifty 50": return FALLBACK_NIFTY_50
        if index_name == "Nifty 100": return FALLBACK_NIFTY_100
        if index_name == "Nifty 200": return FALLBACK_NIFTY_200
        if index_name == "Nifty 500": return FALLBACK_NIFTY_500
        if index_name == "Nifty Next 50": return FALLBACK_NIFTY_100 
        if index_name == "Nifty Midcap 100": return FALLBACK_NIFTY_200 
        return "RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, TATAMOTORS, SBIN, BHARTIARTL"

# --- UI NAVIGATION CONFIGURATION ---
tab_scanner, tab_portfolio, tab_options, tab_tutorial = st.tabs(["🎯 Live Market Scanner", "💼 Active Ledger", "📈 Nifty Options Desk", "📖 Logic Guide"])

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
                    time.sleep(1.5) 
                    intra_data = yf.download(t, period="5d", interval="15m", progress=False)
                    if intra_data is not None and not intra_data.empty:
                        if isinstance(intra_data.columns, pd.MultiIndex):
                            intra_data.columns = intra_data.columns.droplevel(1)
                            
                        intra_data['20_EMA'] = intra_data['Close'].ewm(span=20, adjust=False).mean()
                        last_close = float(intra_data['Close'].iloc[-1])
                        last_ema = float(intra_data['20_EMA'].iloc[-1])
                        
                        if last_close > last_ema:
                            intraday_status = "🔥 ACTIVE"
                        else:
                            intraday_status = "💤 FADING"
                            
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
        
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(BACKUP_DIR, f"Scan_Log_{timestamp}.csv")
            df_results.to_csv(backup_path, index=False)
        except Exception as e:
            pass 
        
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
            if "SQUEEZE" in val: return 'color: #bc5a00; font-weight: bold; background-color: #fff3cd;'
            return ''
            
        def color_intraday(val):
            if val == "🔥 ACTIVE": return 'color: #2ecc71; font-weight: bold;'
            if val == "💤 FADING": return 'color: #e74c3c; font-weight: bold;'
            return ''
            
        def color_vwap(val):
            if "BUYING" in val: return 'color: #2ecc71; font-weight: bold;'
            if "SELLING" in val: return 'color: #e74c3c; font-weight: bold;'
            return ''
            
        styled_df = df_results.style.map(color_signals, subset=['Signal'])\
                                    .map(color_highs, subset=['% from 52W High'])\
                                    .map(color_squeeze, subset=['Volatility Profile'])\
                                    .map(color_intraday, subset=['Live 15m Trend'])\
                                    .map(color_vwap, subset=['Smart Money (VWAP)'])
        
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            height=500,
            hide_index=True,
            column_config={
                "Latest Catalyst": st.column_config.LinkColumn("Latest Catalyst"),
                "% from 52W High": st.column_config.NumberColumn("% from 52W High", format="%.1f%%"),
                "Volume": st.column_config.NumberColumn("Volume", format="%d"),
                "Market RS": st.column_config.NumberColumn("Market RS", format="%.2fx"),
                "Price (₹)": st.column_config.NumberColumn("Price (₹)", format="%.2f"),
                "50 SMA (₹)": st.column_config.NumberColumn("50 SMA (₹)", format="%.2f"),
                "Stop Loss (₹)": st.column_config.NumberColumn("Stop Loss (₹)", format="%.2f"),
                "Target (₹)": st.column_config.NumberColumn("Target (₹)", format="%.2f")
            }
        )
        
        if skipped_count > 0:
            st.caption(f"*(Note: {skipped_count} stocks were automatically excluded from this scan due to lack of historical data).*")
        
        st.markdown("---")
        st.subheader("⚡ 1-Click Paper Execution Deck")
        
        buy_signals_df = df_results[df_results['Signal'].str.contains("BUY", na=False)]
        
        if not buy_signals_df.empty:
            buy_tickers = buy_signals_df['Ticker'].tolist()
            with st.container():
                col_tk, col_qty, col_btn = st.columns([2, 1, 1])
                with col_tk:
                    selected_trade = st.selectbox("Select Breakout Ticker:", buy_tickers)
                with col_qty:
                    trade_qty = st.number_input("Shares to Buy:", min_value=1, value=100, step=10)
                with col_btn:
                    st.write("") 
                    st.write("") 
                    if st.button("📈 Execute Paper Trade", use_container_width=True, type="primary"):
                        trade_data = buy_signals_df[buy_signals_df['Ticker'] == selected_trade].iloc[0]
                        new_row = pd.DataFrame([{
                            'Ticker': selected_trade, 
                            'Type': trade_data['Signal'], 
                            'Entry Price': float(trade_data['Price (₹)']),
                            'Quantity': trade_qty, 
                            'Stop Loss': float(trade_data['Stop Loss (₹)']) if pd.notna(trade_data['Stop Loss (₹)']) else 0.0, 
                            'Target': float(trade_data['Target (₹)']) if pd.notna(trade_data['Target (₹)']) else 0.0
                        }])
                        st.session_state['portfolio'] = pd.concat([st.session_state['portfolio'], new_row], ignore_index=True)
                        st.success(f"Successfully executed {trade_qty} shares of {selected_trade}. Check Tab 2!")
        else:
            st.info("No active buy signals right now. The Execution Deck is resting.")

        st.markdown("---")
        st.subheader("📋 Quick Action Matrix")
        
        sniper_raw = df_results[df_results['Signal'] == "🔥 SNIPER BUY"]['Ticker'].tolist()
        base_raw = df_results[df_results['Signal'].isin(["🚀 BASE BUY", "🚀 BUY SETUP"])]['Ticker'].tolist()
        
        sniper_links = [f'<a href="https://in.tradingview.com/chart/?symbol=NSE:{tk}" target="_blank" style="color:#8e44ad; font-weight:bold; text-decoration:none;">{tk}</a>' for tk in sniper_raw]
        base_links = [f'<a href="https://in.tradingview.com/chart/?symbol=NSE:{tk}" target="_blank" style="color:#2ecc71; font-weight:bold; text-decoration:none;">{tk}</a>' for tk in base_raw]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="padding:15px; border-radius:5px; background-color:#f0f4f8; border-left:5px solid #8e44ad; color:#000000;">'
                        f'<strong>🔥 Sniper Setups:</strong><br><br>'
                        f'{", ".join(sniper_links) if sniper_links else "None right now"}'
                        '</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="padding:15px; border-radius:5px; background-color:#eef9f1; border-left:5px solid #2ecc71; color:#000000;">'
                        f'<strong>🚀 Base Breakouts:</strong><br><br>'
                        f'{", ".join(base_links) if base_links else "None right now"}'
                        '</div>', unsafe_allow_html=True)

        st.markdown("---")
        csv_data = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Manual Export (Log also saved automatically in background)",
            data=csv_data,
            file_name=f"Jaynish_Scanner_Log_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.error("Could not fetch data. The market might be closed or API is temporarily down.")

# =====================================================================
# TAB 2: THE INTERACTIVE PORTFOLIO & P&L LEDGER
# =====================================================================
with tab_portfolio:
    st.header("💼 My Institutional Trade Ledger")
    st.write("Track position scaling and floating net value metrics dynamically across active trade cycles.")

    # --- 1. PERSISTENCE: UPLOAD / DOWNLOAD ---
    col_up, col_dn = st.columns(2)
    with col_up:
        uploaded_file = st.file_uploader("📂 Upload Previous Day's Ledger (CSV):", type="csv")
        if uploaded_file:
            st.session_state['portfolio'] = pd.read_csv(uploaded_file)
            st.rerun()
    
    # --- 2. MANUAL TICKET OVERRIDE ---
    with st.expander("⚙️ Manual Ticket Override (Log Custom Trade)", expanded=False):
        form_col1, form_col2, form_col3 = st.columns(3)
        with form_col1:
            add_tk = st.text_input("Stock Symbol (e.g., RELIANCE):").strip().upper()
            add_type = st.selectbox("Setup Execution Mode:", ["🔥 SNIPER", "🚀 BASE", "⏳ STRATEGIC HOLD"])
        with form_col2:
            add_price = st.number_input("Average Buy Entry Price (₹):", min_value=0.0, step=0.05)
            add_qty = st.number_input("Total Share Quantity:", min_value=1, step=1)
        with form_col3:
            add_sl = st.number_input("Assigned Stop Loss Level (₹):", min_value=0.0, step=0.05)
            add_tgt = st.number_input("Assigned Profit Target Level (₹):", min_value=0.0, step=0.05)
            
        if st.button("💾 Lock Manual Position Into Database", use_container_width=True):
            if add_tk:
                new_row = pd.DataFrame([{
                    'Ticker': add_tk, 'Type': add_type, 'Entry Price': add_price,
                    'Quantity': add_qty, 'Stop Loss': add_sl, 'Target': add_tgt
                }])
                st.session_state['portfolio'] = pd.concat([st.session_state['portfolio'], new_row], ignore_index=True)
                st.rerun()

    # --- 3. REAL-TIME VALUATION & DISPLAY ---
    if not st.session_state['portfolio'].empty:
        portfolio_df = st.session_state['portfolio'].copy()
        unique_tickers = [f"{tk}.NS" for tk in portfolio_df['Ticker'].unique()]
        
        with st.spinner("Synchronizing real-time floating ledger valuations..."):
            live_data = yf.download(unique_tickers, period="1d", progress=False)
            
        # Pricing logic
        live_prices = {}
        for tk in portfolio_df['Ticker'].unique():
            try:
                # Handle single ticker or multiple ticker dataframe index
                col_name = f"{tk}.NS" if len(unique_tickers) > 1 else None
                if col_name and col_name in live_data['Close'].columns:
                    live_prices[tk] = float(live_data['Close'][col_name].iloc[-1])
                else:
                    live_prices[tk] = float(live_data['Close'].iloc[-1])
            except Exception:
                live_prices[tk] = None

        portfolio_df['Live Price (₹)'] = portfolio_df['Ticker'].map(live_prices)
        portfolio_df['Total Investment'] = portfolio_df['Entry Price'] * portfolio_df['Quantity']
        portfolio_df['Current Value'] = portfolio_df['Live Price (₹)'].fillna(portfolio_df['Entry Price']) * portfolio_df['Quantity']
        portfolio_df['Net P&L (₹)'] = portfolio_df['Current Value'] - portfolio_df['Total Investment']
        
        # Display Metrics
        total_cap = portfolio_df['Total Investment'].sum()
        curr_eq = portfolio_df['Current Value'].sum()
        pnl_rs = curr_eq - total_cap
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Deployed Capital", f"₹{total_cap:,.2f}")
        c2.metric("Net Liquid Equity", f"₹{curr_eq:,.2f}")
        c3.metric("Floating Net P&L", f"₹{pnl_rs:,.2f}")

        # Dataframe Styling
        st.dataframe(portfolio_df, use_container_width=True)

        # Export Button
        csv = portfolio_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Monthly Ledger to CSV", csv, "Monthly_Ledger.csv", "text/csv")    
    else:
        st.info("Your active portfolio ledger is completely empty. Execute a paper trade in Tab 1 to track your returns.")

# =====================================================================
# TAB 3: THE NIFTY OPTIONS DESK (STRADDLE/STRANGLE MATRIX)
# =====================================================================
with tab_options:
    st.header("📈 Advanced Options Desk: Volatility Matrix")
    st.write("Quantitative payoff grids for Straddle and Strangle strategies across 7 strikes.")
    
    # 1. Fetch Current Nifty Data
    with st.spinner("Fetching Nifty Options Matrix..."):
        try:
            nifty_data = yf.download("^NSEI", period="1d", progress=False)
            if isinstance(nifty_data.columns, pd.MultiIndex):
                nifty_data.columns = nifty_data.columns.get_level_values(0)
            spot_price = float(nifty_data['Close'].iloc[-1])
        except Exception:
            spot_price = 22000.0 # Fallback if API fails
            
    # Round spot to nearest 50 for realistic Nifty Strikes
    atm_strike = round(spot_price / 50) * 50
    
    col_opt1, col_opt2 = st.columns([1, 2])
    
    with col_opt1:
        st.subheader("Market Context")
        st.metric("Nifty Spot Price", f"₹{spot_price:,.2f}")
        st.metric("Detected ATM Strike", f"₹{atm_strike:,.2f}")
        
        st.markdown("---")
        st.subheader("Strategy Parameters")
        strat_type = st.selectbox("Select Strategy Setup:", ["Long Straddle (Buy)", "Short Straddle (Sell)", "Long Strangle (Buy)", "Short Strangle (Sell)"])
        strike_gap = st.number_input("Strike Interval Gap (e.g., 50, 100):", min_value=50, step=50, value=100)
        
        st.markdown("*(Assuming simulated premiums for calculation)*")
        call_prem = st.number_input("Est. Call Premium (₹):", value=120.0, step=5.0)
        put_prem = st.number_input("Est. Put Premium (₹):", value=115.0, step=5.0)
        lot_size = st.number_input("Lot Size:", value=25) # Nifty Lot Size

    with col_opt2:
        st.subheader(f"7-Strike Payoff Matrix: {strat_type}")
        
        # Generate the 7 Strike Grid
        strikes = [atm_strike + (i * strike_gap) for i in range(-3, 4)]
        
        payoff_data = []
        for exp_price in strikes:
            net_pnl = 0
            
            if "Straddle" in strat_type:
                # Both Call and Put are at ATM Strike
                call_value = max(0, exp_price - atm_strike)
                put_value = max(0, atm_strike - exp_price)
                
                if "Long" in strat_type:
                    net_pnl = (call_value - call_prem) + (put_value - put_prem)
                else: # Short
                    net_pnl = (call_prem - call_value) + (put_prem - put_value)
                    
            elif "Strangle" in strat_type:
                # Strangle uses OTM Strikes (ATM + Gap, ATM - Gap)
                call_strike = atm_strike + strike_gap
                put_strike = atm_strike - strike_gap
                
                call_value = max(0, exp_price - call_strike)
                put_value = max(0, put_strike - exp_price)
                
                if "Long" in strat_type:
                    net_pnl = (call_value - call_prem) + (put_value - put_prem)
                else: # Short
                    net_pnl = (call_prem - call_value) + (put_prem - put_value)
            
            # Convert to actual Rupee P&L per Lot
            total_pnl = net_pnl * lot_size
            
            status = "🟢 PROFIT" if total_pnl > 0 else "🔴 LOSS"
            if total_pnl == 0: status = "⚪ BREAKEVEN"
                
            payoff_data.append({
                "Expiry Nifty Price": f"₹{exp_price:,.0f}",
                "Scenario": "ATM" if exp_price == atm_strike else f"{abs(int(exp_price - atm_strike))} Points Move",
                "Net Points P&L": round(net_pnl, 2),
                "Total ₹ P&L (1 Lot)": f"₹{total_pnl:,.2f}",
                "Status": status
            })
            
        df_payoff = pd.DataFrame(payoff_data)
        
        def highlight_pnl(val):
            if "PROFIT" in val: return 'color: #2ecc71; font-weight:bold;'
            if "LOSS" in val: return 'color: #e74c3c; font-weight:bold;'
            return ''
            
        st.dataframe(df_payoff.style.map(highlight_pnl, subset=['Status']), use_container_width=True, hide_index=True)
        
        if "Long" in strat_type:
            st.info("💡 **Strategy Logic:** You bought both legs. Your maximum loss is limited to the premiums paid. You need a massive breakout/breakdown to achieve unlimited profit.")
        else:
            st.warning("⚠️ **Strategy Logic:** You sold both legs. Your maximum profit is capped at the premium collected. Your risk is technically unlimited if the market moves violently.")

    st.markdown("---")
    st.subheader("📡 Live Options Data Connection Test")
    st.write("Test if Streamlit Cloud can successfully bypass the NSE firewall to fetch live premiums directly.")
    if st.button("Test Live NSE Option Chain Connection"):
        with st.spinner("Spoofing browser and pinging NSE..."):
            result = test_live_option_chain()
            st.write(result)


# =====================================================================
# TAB 4: THE TUTORIAL & STRATEGY GUIDE
# =====================================================================
with tab_tutorial:
    st.header("📖 The Jaynish Multi-Scanner Logic Guide")
    st.write("Welcome to the engine room. Here is exactly how the scanner computes data and generates trading signals.")
    
    st.markdown("---")
    st.subheader("1. The Core Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**📈 RVOL (Relative Volume)**\n\nVolume tells you the *truth* behind a price move. RVOL compares today's trading volume to the 20-day average. \n* **Formula:** `Current Volume / 20-Day Avg Volume`\n* **Logic:** If RVOL is 2.5x, it means institutions are buying 2.5 times heavier than normal. This confirms a true breakout.")
        st.warning("**💥 The SQUEEZE (Volatility Profile)**\n\nThe Squeeze uses Bollinger Bands to find stocks that have gone completely 'quiet'. \n* **Logic:** When a stock stops moving, the Bollinger Bands compress. The engine flags a stock when its bands are 18% tighter than their 100-day average. This indicates silent institutional accumulation right before an explosive expansion phase.")
        st.markdown('<div style="padding:15px; border-radius:5px; background-color:#f9f5ff; border-left:5px solid #8e44ad; color:#000000;">'
                    '<strong>🏦 Smart Money (VWAP)</strong><br><br>'
                    'VWAP (Volume Weighted Average Price) is the holy grail of institutional trading.<br>'
                    '<ul><li><strong>🟢 BUYING:</strong> Current price is ABOVE today\'s VWAP. Large funds are actively paying premium prices to accumulate the stock today.</li>'
                    '<li><strong>🔴 SELLING:</strong> Current price is BELOW today\'s VWAP. Funds are using the breakout volume to quietly offload their shares. Be careful!</li></ul>'
                    '</div>', unsafe_allow_html=True)
    with col2:
        st.success("**📊 Market RS (Relative Strength)**\n\nYou only want to buy the strongest stocks in the market. \n* **Formula:** `Stock 6-Month Return / Nifty 50 6-Month Return`\n* **Logic:** A score of `1.00x` means it matches the Nifty. A score of `1.30x` means it is vastly outperforming the index. Always focus on stocks with RS > 1.00.")
        st.error("**⏱️ MTF Intraday Radar (Live 15m Trend)**\n\nA stock might look great on the Daily chart, but be crashing *today*.\n* **Logic:** When a buy signal triggers, the scanner secretly downloads the 15-minute live chart. If the current price is *above* the 15-minute 20 EMA, it is **🔥 ACTIVE**. If it drops below, momentum is **💤 FADING** and you should hold off buying.")

    st.markdown("---")
    st.subheader("2. How Signals are Generated")
    st.markdown("""
    **🚀 Base Buy Setup (Basic Mode)**
    To trigger a Base Buy, a stock must pass three strict technical rules:
    1. **Trend:** Price must be above the 50-Day SMA, and the 50-Day SMA must be above the 200-Day SMA.
    2. **Momentum:** Today's price must be strictly higher than yesterday's close.
    3. **Volume:** RVOL must be higher than your slider setting (Default: 2.0x).
    
    **🔥 Sniper Buy Setup (Pro Mode)**
    A Sniper setup requires all the rules of a Base Buy, *plus* three elite quantitative filters:
    1. **RSI Filter:** The RSI must be exactly between 60 and 75 (Bullish, but not overbought).
    2. **MACD Filter:** The MACD line must be crossing *above* the Signal Line.
    3. **Pullback Proximity:** The price cannot be more than 8% away from the 50-Day SMA (Prevents buying extended, risky charts).
    """)
    st.markdown("---")
    st.caption("Built for Institutional Momentum Trading | Designed by Jaynish")

# --- GLOBAL AUTO REFRESH LOOP ---
if sleep_time > 0:
    st.sidebar.success(f"⏱️ Auto-Pilot Active: Refreshing in {sleep_time} seconds.")
    time.sleep(sleep_time)
    st.rerun()
