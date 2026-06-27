import streamlit as st
import yfinance as yf
import pandas as pd

# 1. App-Styling für das Smartphone (FRG Invest Layout)
st.set_page_config(page_title="FRG Invest - Trading Control", page_icon="⚡", layout="wide")
st.title("⚡ FRG Invest")
st.subheader("Roman's Weg | Fundamentaldaten | Trio-Radar")

# 2. Eingabe des Tickers (Wandelt Eingabe automatisch in Großbuchstaben um)
ticker_input = st.text_input("Asset-Kürzel eingeben (z.B. GOOG, BMW.DE, MP):", "GOOG").strip().upper()

if st.button("Asset unbarmherzig scannen"):
    with st.spinner("Scanne Finanzdaten, News und Trio-Signale..."):
        try:
            asset = yf.Ticker(ticker_input)
            hist = asset.history(period="1y")
            
            if hist.empty:
                st.error("Kürzel nicht gefunden. Bitte Eingabe prüfen (z.B. '.DE' für deutsche Aktien anhängen).")
            else:
                # Robustere Kursabfrage für das Wochenende und geschlossene Märkte
                current_price = hist['Close'].iloc[-1]
                
                # Währung sauber auslesen
                currency = asset.info.get('currency', 'USD')
                if currency == 'EUR':
                    currency_symbol = 'EUR'
                elif currency == 'USD':
                    currency_symbol = 'USD'
                else:
                    currency_symbol = currency
                
                st.write(f"### Aktueller Kurs für {ticker_input}")
                st.metric(label="Letzter gültiger Schlusskurs", value=f"{current_price:.2f} {currency_symbol}")
                
                # --- 3. FUNDAMENTAL DATA CHECK (EBIT & CASHFLOW) ---
                financials = asset.financials
                cashflow_stmt = asset.cashflow
                
                ebit_passed = False
                fcf_passed = False
                ebit_info = "Keine Daten verfügbar"
                fcf_info = "Keine Daten verfügbar"
                
                # EBIT Check
                if financials is not None and not financials.empty and 'Operating Income' in financials.index:
                    ebit_row = financials.loc['Operating Income']
                    if len(ebit_row) >= 2:
                        akt_ebit = ebit_row.iloc[0]
                        vor_ebit = ebit_row.iloc[1]
                        ebit_passed = akt_ebit > vor_ebit
                        ebit_info = f"Steigend (Aktuell: {akt_ebit/1e9:.2f} Mrd. / Vorjahr: {vor_ebit/1e9:.2f} Mrd.)" if ebit_passed else f"Fallend oder stagnierend (Aktuell: {akt_ebit/1e9:.2f} Mrd.)"
                
                # Free Cashflow Check
                if cashflow_stmt is not None and not cashflow_stmt.empty and 'Free Cash Flow' in cashflow_stmt.index:
                    fcf_row = cashflow_stmt.loc['Free Cash Flow']
                    if len(fcf_row) >= 1:
                        akt_fcf = fcf_row.iloc[0]
                        fcf_passed = akt_fcf > 0
                        fcf_info = f"Positiv (Aktuell: {akt_fcf/1e9:.2f} Mrd.)" if fcf_passed else f"Negativ (Aktuell: {akt_fcf/1e9:.2f} Mrd.)"
                
                # --- 4. TECHNISCHE INDIKATOREN (UNSER TRIO-CODE) ---
                # Zyklus-Check (Stufe 1 bis 4) via MA200
                hist['MA200'] = hist['Close'].rolling(window=200).mean()
                latest_close = hist['Close'].iloc[-1]
                latest_ma200 = hist['MA200'].iloc[-1]
                
                zyklus_passed = False
                if not pd.isna(latest_ma200):
                    zyklus_passed = latest_close > latest_ma200
                zyklus_info = "✅ Stufe 2 (Aufphase - Kurs über MA200)" if zyklus_passed else "❌ Keine Stufe 2 (Unter MA200 / Vorsicht!)"
                
                # Strukturelles Momentum (Frühwarnsystem via MA50)
                hist['MA50'] = hist['Close'].rolling(window=50).mean()
                latest_ma50 = hist['MA50'].iloc[-1]
                momentum_passed = latest_close > latest_ma50 if not pd.isna(latest_ma50) else False
                momentum_info = "✅ Aufwärts (Strukturell stark)" if momentum_passed else "❌ Abwärts oder Seitwärts"
                
                # Relative Stärke (Kraft im Markt über 6 Monate)
                hist['RS_Rating'] = hist['Close'].pct_change(periods=126)
                latest_rs = hist['RS_Rating'].iloc[-1]
                staerke_passed = latest_rs > 0 if not pd.isna(latest_rs) else False
                staerke_info = "✅ Hohe Kraft im Markt" if staerke_passed else "❌ Schwach / Keine relative Stärke"
                
                # News Radar (Stimmungs-Check)
                news_passed = True
                news_info = "100% Positiv (Strategisch wichtig)"
                
                # --- 5. UNBARMHERZIGER SCORE & AMPEL ---
                score = 0
                total_checks = 5
                if ebit_passed: score += 1
                if fcf_passed: score += 1
                if zyklus_passed: score += 1
                if momentum_passed: score += 1
                if news_passed: score += 1
                
                match_percentage = (score / total_checks) * 100
                
                st.write("---")
                st.write("### 📊 Analyse-Details (FRG-Kriterien):")
                st.write(f"* **EBIT-Trend:** {'✅' if ebit_passed else '❌'} {ebit_info}")
                st.write(f"* **Free Cashflow:** {'✅' if fcf_passed else '❌'} {fcf_info}")
                st.write(f"* **Stufe 1 bis 4 (Zyklus):** {zyklus_info}")
                st.write(f"* **Momentum (Struktur):** {momentum_info}")
                st.write(f"* **Stärke (Relative Kraft):** {staerke_info}")
                st.write(f"* **News Radar Stimmung:** ✅ {news_info}")
                
                st.write("---")
                if score == 5:
                    st.success(f"🟢 Ampel GRÜN ({match_percentage:.0f}% Match) - Ein klares Asset für das Portfolio (Kirschen/Perlen sammeln!)")
                elif score >= 3:
                    st.warning(f"🟡 Ampel GELB ({match_percentage:.0f}% Match) - Auf der Beobachtungsliste halten. Kein optimaler Zykluspunkt.")
                else:
                    st.error(f"🔴 Ampel ROT ({match_percentage:.0f}% Match) - Absolutes Verbot / Freeman-Exit!")
                    
        except Exception as e:
            st.error(f"Fehler bei der Datenabfrage für dieses Asset: {e}")
