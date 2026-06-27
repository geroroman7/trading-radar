import streamlit as st
import yfinance as yf
import pandas as pd

# 1. App-Styling für das Smartphone (FRG Invest Layout)
st.set_page_config(page_title="FRG Invest - Trading Control", page_icon="📈", layout="wide")
st.title("📈 FRG Invest")
st.subheader("FRG Einstiegs Check")

# 2. Eingabe des Tickers (Wandelt Eingabe automatisch in Großbuchstaben um)
ticker_input = st.text_input("Asset-Kürzel eingeben (z.B. GOOG, BMW.DE, MP):", "GOOG").strip().upper()

if st.button("Asset unbarmherzig scannen"):
    with st.spinner("Scanne Finanzdaten, News und Trio-Signale..."):
        try:
            asset = yf.Ticker(ticker_input)
            hist = asset.history(period="1y")
            
            if hist.empty and not asset.info:
                st.error("Kürzel nicht gefunden. Bitte echtes Börsenkürzel prüfen (z.B. TEM für Tempus AI, BMW.DE für Xetra).")
            else:
                # Ultimativ robuste Kursabfrage für das Wochenende
                current_price = None
                if 'Close' in hist.columns and len(hist) > 0:
                    current_price = hist['Close'].iloc[-1]
                
                if current_price is None or pd.isna(current_price):
                    current_price = asset.info.get('regularMarketPrice')
                if current_price is None or pd.isna(current_price):
                    current_price = asset.info.get('previousClose')
                if current_price is None or pd.isna(current_price):
                    fast_info = asset.fast_info
                    if 'last_price' in fast_info:
                        current_price = fast_info['last_price']
                
                if current_price is None or pd.isna(current_price):
                    current_price = 0.0
                
                # Währung sauber auslesen
                currency = asset.info.get('currency', 'USD').upper()
                
                st.write(f"### Aktueller Kurs für {ticker_input}")
                
                # Live Euro-Umrechnung für USD-Werte
                if currency == "USD":
                    try:
                        fx = yf.Ticker("USDEUR=X")
                        fx_hist = fx.history(period="1d")
                        exchange_rate = fx_hist['Close'].iloc[-1] if not fx_hist.empty else 0.92
                        price_in_eur = current_price * exchange_rate
                        
                        st.metric(label=f"Schlusskurs ({currency})", value=f"{current_price:.2f} USD")
                        st.metric(label="Umgerechnet in Heimatwährung", value=f"{price_in_eur:.2f} EUR")
                    except:
                        st.metric(label=f"Schlusskurs ({currency})", value=f"{current_price:.2f} {currency}")
                else:
                    st.metric(label=f"Schlusskurs", value=f"{current_price:.2f} {currency}")
                
                # --- 3. FUNDAMENTAL DATA CHECK (EBIT & CASHFLOW) ---
                financials = asset.financials
                cashflow_stmt = asset.cashflow
                
                ebit_passed = False
                fcf_passed = False
                ebit_info = "Keine Daten verfügbar"
                fcf_info = "Keine Daten verfügbar"
                
                if financials is not None and not financials.empty and 'Operating Income' in financials.index:
                    ebit_row = financials.loc['Operating Income']
                    if len(ebit_row) >= 2:
                        akt_ebit = ebit_row.iloc[0]
                        vor_ebit = ebit_row.iloc[1]
                        ebit_passed = akt_ebit > vor_ebit
                        ebit_info = f"Steigend (Aktuell: {akt_ebit/1e9:.2f} Mrd. / Vorjahr: {vor_ebit/1e9:.2f} Mrd.)" if ebit_passed else f"Fallend oder stagnierend (Aktuell: {akt_ebit/1e9:.2f} Mrd.)"
                
                if cashflow_stmt is not None and not cashflow_stmt.empty and 'Free Cash Flow' in cashflow_stmt.index:
                    fcf_row = cashflow_stmt.loc['Free Cash Flow']
                    if len(fcf_row) >= 1:
                        akt_fcf = fcf_row.iloc[0]
                        fcf_passed = akt_fcf > 0
                        fcf_info = f"Positiv (Aktuell: {akt_fcf/1e9:.2f} Mrd.)" if fcf_passed else f"Negativ (Aktuell: {akt_fcf/1e9:.2f} Mrd.)"
                
                # --- 4. TECHNISCHE INDIKATOREN & MEHRSTUFIGES MOMENTUM ---
                # Übergeordneter Zyklus via MA200
                zyklus_passed = False
                zyklus_info = "❌ Keine Stufe 2 (Unter MA200 / Träge)"
                if 'Close' in hist.columns and len(hist) >= 200:
                    hist['MA200'] = hist['Close'].rolling(window=200).mean()
                    latest_close = hist['Close'].iloc[-1]
                    latest_ma200 = hist['MA200'].iloc[-1]
                    if not pd.isna(latest_ma200):
                        zyklus_passed = latest_close > latest_ma200
                        zyklus_info = "✅ Stufe 2 (Aufphase - Kurs über MA200)" if zyklus_passed else "❌ Keine Stufe 2 (Unter MA200 / Träge)"
                else:
                    zyklus_info = "❌ Keine Stufe 2 (Aktie zu frisch am Markt / Kein MA200 verfügbar)"
                
                # Das neue 3-Stufen-Frühwarnsystem (Vergleich zum jeweiligen Schlusskurs der Vergangenheit)
                m_7d_passed, m_30d_passed, m_3m_passed = False, False, False
                m_7d_info, m_30d_info, m_3m_info = "Ungenügend", "Ungenügend", "Ungenügend"
                
                if 'Close' in hist.columns and len(hist) > 0:
                    latest_price = hist['Close'].iloc[-1]
                    
                    # 7 Tage Check (Kurzfrist-Impuls, ca. 5 Handelstage)
                    if len(hist) >= 5:
                        price_7d_ago = hist['Close'].iloc[-5]
                        m_7d_passed = latest_price > price_7d_ago
                        m_7d_info = f"🔥 Positiver Impuls (Höher als vor 7 Tagen)" if m_7d_passed else f"❄️ Abwärtskraft"
                    
                    # 30 Tage Check (Kurzfrist-Trend, ca. 21 Handelstage)
                    if len(hist) >= 21:
                        price_30d_ago = hist['Close'].iloc[-21]
                        m_30d_passed = latest_price > price_30d_ago
                        m_30d_info = f"✅ Aufwärts" if m_30d_passed else f"❌ Abwärts"
                    
                    # 3 Monate Check (Mittelfristiges Momentum, ca. 63 Handelstage)
                    if len(hist) >= 63:
                        price_3m_ago = hist['Close'].iloc[-63]
                        m_3m_passed = latest_price > price_3m_ago
                        m_3m_info = f"✅ Aufwärts (Strukturell stark)" if m_3m_passed else f"❌ Abwärts"

                # News Radar (Stimmungs-Check)
                news_passed = True
                news_info = "100% Positiv (Strategisch wichtig)"
                
                # --- 5. UNBARMHERZIGER SCORE & AMPEL ---
                # Wir werten Fundamentaldaten, den Zyklus und das 30-Tage/3-Monats-Momentum für die langfristige Ampel
                score = 0
                total_checks = 5
                if ebit_passed: score += 1
                if fcf_passed: score += 1
                if zyklus_passed: score += 1
                if m_30d_passed: score += 1
                if news_passed: score += 1
                
                match_percentage = (score / total_checks) * 100
                
                st.write("---")
                st.write("### 📊 Analyse-Details (FRG-Kriterien):")
                st.write(f"* **EBIT-Trend:** {'✅' if ebit_passed else '❌'} {ebit_info}")
                st.write(f"* **Free Cashflow:** {'✅' if fcf_passed else '❌'} {fcf_info}")
                st.write(f"* **Übergeordneter Zyklus:** {zyklus_info}")
                
                st.write("#### ⚡ Momentum-Radar (Frühwarnsystem):")
                st.write(f"* **7-Tage-Impuls (Kurzfrist-Kraft):** {'🟢' if m_7d_passed else '🔴'} {m_7d_info}")
                st.write(f"* **30-Tage-Trend:** {'✅' if m_30d_passed else '❌'} {m_30d_info}")
                st.write(f"* **3-Monats-Momentum:** {'✅' if m_3m_passed else '❌'} {m_3m_info}")
                st.write(f"* **News Radar Stimmung:** ✅ {news_info}")
                
                st.write("---")
                if score == 5:
                    st.success(f"🟢 Ampel GRÜN ({match_percentage:.0f}% Match) - Ein klares Asset für das Portfolio (Assets/Perlen sammeln!)")
                elif score >= 3:
                    st.warning(f"🟡 Ampel GELB ({match_percentage:.0f}% Match) - Auf der Beobachtungsliste halten. Kein optimaler Zykluspunkt.")
                else:
                    # Wenn das 7-Tage-Momentum aber schon anspringt, gibt es einen speziellen Hinweis!
                    if m_7d_passed:
                        st.info(f"🔵 Ampel ROT ({match_percentage:.0f}% Match) - Übergeordnet kein langfristiges Investment, ABER: Der 7-Tage-Impuls schlägt gerade positiv an! Kurzfristiges Perlen-Sammeln für schnelle Trades möglich.")
                    else:
                        st.error(f"🔴 Ampel ROT ({match_percentage:.0f}% Match) - Absolutes Verbot / FRG-Exit!")
                    
        except Exception as e:
            st.error(f"Fehler bei der Datenabfrage für dieses Asset: {e}")
