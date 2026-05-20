import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
import io
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Jaynish Multi-Scanner", layout="wide")

st.title("🏆 Jaynish Multi-Scanner")
st.write("Real-time automated dashboard tracking institutional momentum setups.")

def tick(val):
    return float(round(float(val) * 20) / 20)

# --- LIVE NSE AUTO-UPDATER ---
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
            raise Exception("Blocked")
    except Exception:
        # Emergency backup tickers if connection is dropped
        return "RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, TATAMOTORS, SBIN, BHARTIARTL"

st.sidebar.header("⚙️ Scanner Settings")

app_mode = st.sidebar.radio(
    "Select Scanner Mode:",
    ["📊 Basic Version (Trend & Volume)", "🔥 Pro Version (Sniper Metrics)"]
)
st.sidebar.markdown("---")

index_choice = st.sidebar.selectbox(
    "Select Market Index:",
    ["Nifty 50", "Nifty Next 50", "Nifty 100", "Nifty Midcap 100", "Nifty 200", "Nifty 500", "Custom List"]
)

if index_choice == "Custom List":
    user_stocks = st.sidebar.text_area("Watchlist (Separate with commas):", "RELIANCE, TCS, INFY", height=150)
    ticker_list = [f"{s.strip().upper()}.NS" for s in user_stocks.split(",") if s.strip()]
else:
    raw_stocks = fetch_nse_list(index_choice)
    ticker_list = [f"{s.strip().upper()}.NS" for s in raw_stocks.split(",") if s.strip()]

st.sidebar.markdown("---")
volume_multiplier = st.sidebar.slider("RVOL Breakout Multiplier", 1.5, 3.0, 2.0, 0.1)
risk_pct = st.sidebar.slider("Stop Loss Risk %", 3.0, 8.0, 5.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Auto-Pilot")
refresh_choice = st.sidebar.selectbox("Auto-Refresh Interval:", ["Off", "1 Minute", "2 Minutes", "5 Minutes", "10 Minutes"])

refresh_dict = {"Off": 0, "1 Minute": 60, "2 Minutes": 120, "5 Minutes": 300, "10 Minutes": 600}
sleep_time = refresh_dict[refresh_choice]

results = []
skipped_count = 0

# Add the baseline Nifty index to our batch query to compute real-time relative strength
download_list = ticker_list.copy()
if "^NSEI" not in download_list:
    download_list.append("^NSEI")

with st.spinner(f"Downloading {index_choice} live market matrix..."):
    data = yf.download(download_list, period="1y", group_by='ticker', threads=False, progress=False)

# Compute benchmark performance for the baseline index
try:
    nifty_df = data["^NSEI"].dropna()
    nifty_6m_old = nifty_df['Close'].iloc[-126] if len(nifty_df) >= 126 else nifty_df['Close'].iloc[0]
    nifty_benchmark_ret = (float(nifty_df['Close'].iloc[-1]) - float(nifty_6m_old)) / float(nifty_6m_old)
except Exception:
    nifty_benchmark_ret = 0.10 # Hard fallback reference if benchmark download encounters lag

my_bar = st.progress(0, text=f"Analyzing setups using {app_mode.split(' ')[1]}...")
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
        
        # Mathematical Core Metrics
        df['50_SMA'] = df['Close'].rolling(window=50).mean()
        df['200_SMA'] = df['Close'].rolling(window=200).mean()
        df['20_Vol_SMA'] = df['Volume'].rolling(window=20).mean()
        
        # Volatility Squeeze Math (Bollinger Band Compression Engine)
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
        
        # Vol Squeeze Logic evaluation
        current_bw = float(latest['BB_Width'])
        avg_bw = float(latest['BB_Width_SMA'])
        is_squeezing = current_bw < (avg_bw * 0.82)
        vol_status = "💥 SQUEEZE" if is_squeezing else "Normal"
        
        # Relative Strength Matrix Math (6-Month Asset Performance vs Benchmark Index)
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

        row_data = {
            "Ticker": t.replace(".NS", ""),
            "Signal": signal,
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
    df_results.index = df_results.index + 1 
    
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
        
    styled_df = df_results.style.map(color_signals, subset=['Signal'])\
                                .map(color_highs, subset=['% from 52W High'])\
                                .map(color_squeeze, subset=['Volatility Profile'])
    
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        height=600,
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
    st.subheader("📋 Quick Action Summary")
    
    sniper_raw = df_results[df_results['Signal'] == "🔥 SNIPER BUY"]['Ticker'].tolist()
    base_raw = df_results[df_results['Signal'].isin(["🚀 BASE BUY", "🚀 BUY SETUP"])]['Ticker'].tolist()
    
    sniper_links = [f'<a href="https://in.tradingview.com/chart/?symbol=NSE:{tk}" target="_blank" style="color:#8e44ad; font-weight:bold; text-decoration:none;">{tk}</a>' for tk in sniper_raw]
    base_links = [f'<a href="https://in.tradingview.com/chart/?symbol=NSE:{tk}" target="_blank" style="color:#2ecc71; font-weight:bold; text-decoration:none;">{tk}</a>' for tk in base_raw]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="padding:15px; border-radius:5px; background-color:#f0f4f8; border-left:5px solid #8e44ad;">'
                    f'<strong>🔥 Sniper Setups:</strong><br><br>'
                    f'{", ".join(sniper_links) if sniper_links else "None right now"}'
                    '</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="padding:15px; border-radius:5px; background-color:#eef9f1; border-left:5px solid #2ecc71;">'
                    f'<strong>🚀 Base Breakouts:</strong><br><br>'
                    f'{", ".join(base_links) if base_links else "None right now"}'
                    '</div>', unsafe_allow_html=True)

    # --- THE DAILY LOG EXPORTER ENGINE ---
    st.markdown("---")
    csv_data = df_results.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Current Scan to CSV (Excel Log)",
        data=csv_data,
        file_name=f"Jaynish_Scanner_Log_{time.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.error("Could not fetch data. The market might be closed or API is temporarily down.")

if sleep_time > 0:
    st.sidebar.success(f"⏱️ Auto-Pilot Active: Refreshing in {sleep_time} seconds.")
    time.sleep(sleep_time)
    st.rerun()
