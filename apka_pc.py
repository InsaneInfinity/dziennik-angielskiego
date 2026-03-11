import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- KONFIGURACJA ---
# Twój link do arkusza Google
URL_ARKUSZA = "https://docs.google.com/spreadsheets/d/1uYtQfDf1BjS5eoFAEn8DEmfv0ukeC6IPhqVZlso_Fr8/edit?usp=sharing"

st.set_page_config(page_title="Manager Lektora PRO", layout="wide", page_icon="📈")

# Połączenie z Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Funkcja do wczytywania danych
def wczytaj_dane():
    try:
        # Odczytujemy dane z arkusza (pierwsze 4 kolumny)
        return conn.read(spreadsheet=URL_ARKUSZA, usecols=[0, 1, 2, 3]).dropna(how="all")
    except:
        # Jeśli arkusz jest pusty lub ma błąd, zwracamy pustą tabelę
        return pd.DataFrame(columns=["Data", "Lekcje_80", "Lekcje_120", "Suma"])

df = wczytaj_dane()

# --- PANEL BOCZNY (DODAWANIE) ---
st.sidebar.header("➕ Dodaj Nowe Lekcje")
with st.sidebar.form("dodaj_form", clear_on_submit=True):
    d = st.date_input("Data zajęć", datetime.now())
    l80 = st.number_input("Lekcje 1-os (80zł)", min_value=0, step=1)
    l120 = st.number_input("Lekcje 2-os (120zł)", min_value=0, step=1)
    submit = st.form_submit_button("Zatwierdź i Zapisz")

    if submit:
        # Przygotowanie nowego wiersza
        nowy_wiersz = pd.DataFrame({
            "Data": [d.strftime('%Y-%m-%d')],
            "Lekcje_80": [l80],
            "Lekcje_120": [l120],
            "Suma": [(l80 * 80) + (l120 * 120)]
        })
        
        # Łączymy stare dane z nowymi
        updated_df = pd.concat([df, nowy_wiersz], ignore_index=True)
        
        # WYSYŁAMY DO GOOGLE SHEETS
        conn.update(spreadsheet=URL_ARKUSZA, data=updated_df)
        
        st.sidebar.success("Zapisano w Arkuszu Google!")
        st.cache_data.clear() # Czyścimy pamięć, żeby od razu pobrał nowe dane
        st.rerun()

# --- GŁÓWNY EKRAN ---
st.title("📊 System Rozliczeń (Google Sheets)")
st.info("Dane są zapisywane w Twoim arkuszu Google. Nic nie zginie!")

# Filtry zakresu dat
st.subheader("🔍 Wybierz okres raportu")
c1, c2 = st.columns(2)
with c1:
    data_od = st.date_input("Od kiedy:", datetime.now() - timedelta(days=30))
with c2:
    data_do = st.date_input("Do kiedy:", datetime.now())

if not df.empty:
    # Upewniamy się, że kolumna Data to faktycznie daty
    df['Data'] = pd.to_datetime(df['Data'])
    df_filtered = df[(df['Data'].dt.date >= data_od) & (df['Data'].dt.date <= data_do)].sort_values("Data")

    # METRYKI (SUMY)
    st.divider()
    m1, m2, m3 = st.columns(3)
    total_80 = df_filtered["Lekcje_80"].sum()
    total_120 = df_filtered["Lekcje_120"].sum()
    total_kasa = df_filtered["Suma"].sum()

    m1.metric("Lekcje 80zł", f"{int(total_80)} h")
    m2.metric("Lekcje 120zł", f"{int(total_120)} h")
    m3.metric("ZAROBEK RAZEM", f"{total_kasa:,.2f} PLN")

    # WIDOKI
    tab1, tab2 = st.tabs(["📅 Wykres Zarobków", "📂 Tabela Wszystkich Wpisów"])
    with tab1:
        st.bar_chart(data=df_filtered, x="Data", y="Suma")
    with tab2:
        st.dataframe(df, use_container_width=True)
else:
    st.warning("Arkusz jest jeszcze pusty. Dodaj pierwszy wpis po lewej!")
