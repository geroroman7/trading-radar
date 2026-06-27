import streamlit as st
import yfinance as yf
import pandas as pd

# 1. App-Styling für das Smartphone
st.set_page_config(page_title="Roman's Trading Control", page_icon="⚡", layout="wide")
st.title("⚡ Roman's Trading-Radar V2")
st.subheader("Trio | Fundamentaldaten | 360° News")

# 2. Eingabe des Tickers
ticker_input = st.text_input("Aktien-Kürzel eingeben (z.B. GOOG, BMW.DE, MP):", "GOOG").upper()

if st.button("Asset unbarmherzig scannen"):
    with st.spinner("Scanne Finanzdaten, News und Trio-Signale..."):
        try:
            asset = yf.Ticker(ticker_input)
            hist = asset.history(period="1y")
            
            if hist.empty:
                st.error("Ticker nicht gefunden. Bitte Kürzel prüfen.")
            else:
                current_price = hist['Close'].iloc[-1]
                
                # --- 3. FUNDAMENTAL DATA CHECK (EBIT & CASHFLOW) ---
                financials = asset.financials
                cashflow_stmt = asset.cashflow
                
                ebit_passed = False
                fcf_passed = False
                ebit_info = "Keine Daten"
                fcf_info = "Keine Daten"
                
                if financials is not None and not financials.empty and 'Operating Income' in financials.index:
                    ebit_years = financials.loc['Operating Income']
                    if len(ebit_years) >= 2:
                        ebit_passed = ebit_years.iloc[0] > ebit_years.iloc[1]
                        ebit_info = f"Aktuell: {ebit_years.iloc[0]/1e9:.2f} Mrd. (Vorjahr: {ebit_years.iloc[1]/1e9:.2f} Mrd.)"
                
                if cashflow_stmt is not None and not cashflow_stmt.empty and 'Free Cash Flow' in cashflow_stmt.index:
                    fcf_years = cashflow_stmt.loc['Free Cash Flow']
                    if len(fcf_years) >= 1:
                        fcf_passed = fcf_years.iloc[0] > 0
                        fcf_info = f"Aktuell: {fcf_years.iloc[0]/1e9:.2f} Mrd."

                # --- 4. TRIO CORE LOGIC (WEINSTEIN, OLIVER, O'NEIL) ---
                hist['MA200'] = hist['Close'].rolling(window=200).mean()
                weinstein_passed = current_price > hist['MA200'].iloc[-1] if not pd.isna(hist['MA200'].iloc[-1]) else False
                
                hist['MA20'] = hist['Close'].rolling(window=20).mean()
                hist['MA50'] = hist['Close'].rolling(window=50).mean()
                momentum_passed = hist['MA20'].iloc[-1] > hist['MA50'].iloc[-1]
                
                year_high, year_low = hist['Close'].max(), hist['Close'].min()
                rs_score = ((current_price - year_low) / (year_high - year_low)) * 100
                oneil_passed = rs_score > 70
                
                # Score-Berechnung
                fundamental_score = 30 if (ebit_passed and fcf_passed) else (15 if (ebit_passed or fcf_passed) else 0)
                trio_score = 0
                if weinstein_passed: trio_score += 25
                if momentum_passed: trio_score += 25
                if oneil_passed: trio_score += 20
                total_score = fundamental_score + trio_score
                
                # --- 5. 360° NEWS SENTIMENT RADAR ---
                news_list = asset.news
                bad_news_count = 0
                gravierende_news = []
                
                crash_words = [
                    "crash", "drop", "warn", "loss", "fall", "skandal", "geopolitical",
                    "miss", "earnings miss", "disappointing", "guidance cut",
                    "ceo steps down", "ceo resigns", "management change", "resignation",
                    "spinoff", "split", "restructuring", "carve-out",
                    "dilution", "share issuance", "capital increase", "diluted"
                ]
                
                if news_list:
                    for news in news_list[:5]:
                        title = news.get('title', '').lower()
                        if any(word in title for word in crash_words):
                            bad_news_count += 1
                            gravierende_news.append(news.get('title'))
                
                news_score = max(0, 100 - (bad_news_count * 25))
                
                # --- 6. SMARTPHONE DASHBOARD AUSGABE ---
                st.markdown("---")
                st.metric(label=f"Kurs für {ticker_input}", value=f"{current_price:.2f} USD/EUR")
                
                if total_score >= 75 and news_score >= 75:
                    st.success(f"🟢 Ampel GRÜN ({total_score}% Match) - Bereit zum Traden!")
                elif total_score >= 45 and news_score >= 50:
                    st.warning(f"🟡 Ampel GELB ({total_score}% Match) - Keine Dynamik / Beobachten.")
                else:
                    st.error(f"🔴 Ampel ROT ({total_score}% Match) - Absolutes Verbot / Freeman-Exit!")
                
                st.write("### 📊 Analyse-Details:")
                st.write(f"- **EBIT-Trend:** {'✅ Steigend' if ebit_passed else '❌ Fallend/Stagnierend'} ({ebit_info})")
                st.write(f"- **Free Cashflow:** {'✅ Positiv' if fcf_passed else '❌ Negativ (Geldverbrennung!)'} ({fcf_info})")
                st.write(f"- **Weinstein Phase 2:** {'✅ Ja (Über MA200)' if weinstein_passed else '❌ Nein (Unter MA200)'}")
                st.write(f"- **Oliver Momentum:** {'✅ Aufwärts' if momentum_passed else '❌ Abwärts/Seitwärts'}")
                st.write(f"- **O'Neil Relative Stärke:** {'✅ Stark (Top 30%)' if oneil_passed else '❌ Schwach'}")
                st.write(f"- **News Radar Stimmung:** {news_score}% Positiv")
                
                if gravierende_news:
                    st.markdown("---")
                    st.write("⚠️ **Kritische Schlagzeilen entdeckt:**")
                    for n in gravierende_news:
                        st.write(f"- *{n}*")
                        
        except Exception as e:
            st.error(f"Fehler beim Scannen: {str(e)}")
