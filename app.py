# --- TAB 4: NIFTY OPTIONS DESK (FIXED) ---
with tab_options:
    st.header("📈 Nifty Options Desk")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Nifty Trend")
        # Fetch data specifically for Nifty
        nifty_data = yf.download("^NSEI", period="1d", progress=False)
        
        # FIX: Check if data is empty and handle the dataframe structure
        if not nifty_data.empty:
            # Flatten columns if necessary (common yfinance fix)
            if isinstance(nifty_data.columns, pd.MultiIndex):
                nifty_data.columns = nifty_data.columns.get_level_values(0)
            
            latest_nifty = float(nifty_data['Close'].iloc[-1])
            st.metric("Nifty Spot", f"₹{latest_nifty:,.2f}")
        else:
            st.error("Nifty data unavailable.")
            
    with col2:
        st.subheader("Spread Calculator")
        entry = st.number_input("Option Premium:", min_value=0.0)
        if entry > 0: 
            st.write(f"Target (1:2 RR): ₹{entry * 2:,.2f}")
