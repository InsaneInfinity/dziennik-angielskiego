import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- USTAWIENIA I PLIK ---
PLIK_CSV = "baza_lekcji_strona.csv"

# Funkcja do ładowania danych z pliku
def wczytaj_dane():
    if os.path.exists(PLIK_CSV):
        df = pd.read_csv(PLIK_CSV)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    return pd.DataFrame(columns=["Data", "Lekcje_80", "Lekcje_120", "Suma"])

# --- START APKI ---
st.set_page_config(page_title="Dziennik Lektora PRO", layout="wide")

# Ładujemy dane do pamięci podręcznej strony
if 'df' not in st.session_state:
    st.session_state.df = wczytaj_dane()

# --- PANEL BOCZNY (DODAWANIE) ---
st.sidebar.header("➕ Dodaj Lekcje")
with st.sidebar.form("dodaj_form", clear_on_submit=True):
    d = st.date_input("Data", datetime.now())
    l80 = st.number_input("Lekcje 80zł", min_value=0, step=1)
    l120 = st.number_input("Lekcje 120zł", min_value=0, step=1)
    submit = st.form_submit_button("Zapisz w bazie")

    if submit:
        nowy_wiersz = pd.DataFrame({
            "Data": [pd.to_datetime(d)],
            "Lekcje_80": [l80],
            "Lekcje_120": [l120],
            "Suma": [(l80 * 80) + (l120 * 120)]
        })
        st.session_state.df = pd.concat([st.session_state.df, nowy_wiersz], ignore_index=True)
        # Zapis do pliku na dysku PC
        st.session_state.df.to_csv(PLIK_CSV, index=False)
        st.sidebar.success("Zapisano pomyślnie!")

# --- GŁÓWNY EKRAN ---
st.title("📊 System Rozliczeń Lektora")

# Filtry zakresu dat
st.subheader("🔍 Wybierz okres raportu")
c1, c2 = st.columns(2)
with c1:
    data_od = st.date_input("Od:", datetime.now() - timedelta(days=30))
with c2:
    data_do = st.date_input("Do:", datetime.now())

# Filtrowanie danych
if not st.session_state.df.empty:
    df_filtered = st.session_state.df[
        (st.session_state.df['Data'].dt.date >= data_od) & 
        (st.session_state.df['Data'].dt.date <= data_do)
    ].sort_values("Data")

    # --- PODSUMOWANIE STATYSTYCZNE ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    total_80 = df_filtered["Lekcje_80"].sum()
    total_120 = df_filtered["Lekcje_120"].sum()
    total_kasa = df_filtered["Suma"].sum()

    m1.metric("Lekcje 1-os (80zł)", f"{int(total_80)} h")
    m2.metric("Lekcje 2-os (120zł)", f"{int(total_120)} h")
    m3.metric("ŁĄCZNY ZAROBEK", f"{total_kasa:,.2f} PLN")

    # --- TABELE I WYKRESY ---
    tab1, tab2, tab3 = st.tabs(["📅 Widok Dzienny", "📆 Tygodniowo", "📂 Wszystkie Dane"])

    with tab1:
        st.bar_chart(data=df_filtered, x="Data", y="Suma")
        st.dataframe(df_filtered, use_container_width=True)

    with tab2:
        # Grupowanie po tygodniu
        df_tydzien = df_filtered.resample('W-MON', on='Data').sum()
        st.write("Suma zarobków w podziale na tygodnie (początek tygodnia to Poniedziałek):")
        st.table(df_tydzien[['Lekcje_80', 'Lekcje_120', 'Suma']])

    with tab3:
        st.write("Pełna historia wpisów:")
        st.write(st.session_state.df)
        if st.button("Usuń ostatni wpis"):
            st.session_state.df = st.session_state.df[:-1]
            st.session_state.df.to_csv(PLIK_CSV, index=False)
            st.rerun()

else:

    st.info("Baza danych jest pusta. Użyj panelu po lewej, aby dodać pierwsze lekcje.")
