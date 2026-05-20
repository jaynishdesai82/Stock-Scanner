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
    return f"{round(float(val) * 20) / 20:.2f}"

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
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(urls[index_name], headers=headers, timeout=5)
        df = pd.read_csv(io.StringIO(response.text))
        return ", ".join(df['Symbol'].tolist())
    except Exception:
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

with st.spinner(f"Downloading {index_choice} live data (This may take a moment)..."):
    data = yf.download(ticker_list, period="1y", group_by='ticker', threads=False, progress=False)
    
my_bar = st.progress(0, text=f"Analyzing setups using {app_mode.split(' ')[1]}...")
total_stocks = len(ticker_list)

for i, t in enumerate(ticker_list):
    try:
        if len(ticker_list) == 1:
            df = data.dropna()
        else:
            df = data[t].dropna()
            
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
        
        # NEW: 52-Week High Calculation
        high_52w = float(df['High'].max())
        pct_from_52w = ((current_price - high_52w) / high_52w) * 100
        
        trend_ok = (current_price > sma_50) and (sma_50 > sma_200)
        volume_ok = current_volume > (vol_sma * volume_multiplier)
        price_ok = current_price > float(prev_close)
        
        sl_price = current_price * (1 - (risk_pct / 100))
        target_3r = current_price * (1 + (risk_pct * 3 / 100))
        
        # Determine Signal
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
        
        # NEW: Smart News Fetcher (Only fetches for Buy Setups to save time)
        latest_news = "---"
        if "BUY" in signal:
            try:
                stock_info = yf.Ticker(t)
                news_list = stock_info.news
                if news_list and len(news_list) > 0:
                    title = news_list[0].get('title', 'News Link')
                    link = news_list[0].get('link', '#')
                    # Formats as a clickable markdown link
                    latest_news = f"[{title[:40]}...]({link})" 
            except Exception:
                latest_news = "News unavailable"

        # Build Row Data
        row_data = {
            "Ticker": t.replace(".NS", ""),
            "Signal": signal,
            "Price (₹)": tick(current_price),
            "% from 52W High": f"{pct_from_52w:.1f}%",
            "Volume": f"{int(current_volume):,}",
            "RVOL": round(current_volume / vol_sma, 2)
        }
        
        if "Pro Version" in app_mode:
            row_data.update({
                "RSI": round(rsi, 1),
                "MACD": "UP 📈" if macd_bullish else "DOWN 📉",
            })
            
        row_data.update({
            "50 SMA (₹)": tick(sma_50),
            "Stop Loss": tick(sl_price) if show_levels else "---",
            "Target": tick(target_3r) if show_levels else "---",
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
        try:
            num = float(val.replace('%', ''))
            if num >= -5.0: return 'color: #2ecc71; font-weight: bold;' # Near highs
            if num <= -30.0: return 'color: #e74c3c;' # Beaten down
            return ''
        except: return ''
        
    styled_df = df_results.style.map(color_signals, subset=['Signal']).map(color_highs, subset=['% from 52W High'])
    
    # Configure Streamlit to render markdown links properly
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        height=600,
        column_config={
            "Latest Catalyst": st.column_config.LinkColumn("Latest Catalyst")
        }
    )
    
    if skipped_count > 0:
        st.caption(f"*(Note: {skipped_count} stocks were automatically excluded from this scan due to lack of historical data).*")
    
    st.markdown("---")
    st.subheader("📋 Quick Action Summary")
    
    sniper_stocks = df_results[df_results['Signal'] == "🔥 SNIPER BUY"]['Ticker'].tolist()
    base_buy_stocks = df_results[df_results['Signal'].isin(["🚀 BASE BUY", "🚀 BUY SETUP"])]['Ticker'].tolist()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**🔥 Sniper Setups:**\n\n{', '.join(sniper_stocks) if sniper_stocks else 'None right now'}")
    with col2:
        st.success(f"**🚀 Base Breakouts:**\n\n{', '.join(base_buy_stocks) if base_buy_stocks else 'None right now'}")

else:
    st.error("Could not fetch data. The market might be closed or API is temporarily down.")

if sleep_time > 0:
    st.sidebar.success(f"⏱️ Auto-Pilot Active: Refreshing in {sleep_time} seconds.")
    time.sleep(sleep_time)
    st.rerun()
