import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Lider Logistik", layout="wide")
st.title("📦 Yuk Kirimi Hisoblash")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    uploaded_file = st.file_uploader("Excel yoki CSV fayl yuklang", type=["xlsx","csv"])
    
    # step=0.01 va format="%.2f" qoldiqni saqlashga yordam beradi
    yol_kira = st.number_input("Jami Yo'l kira ($)", value=1800.0, step=0.01, format="%.2f")
    kurs_naqd = st.number_input("Naqd kurs (sertifikat)", value=12900.0, step=0.01, format="%.2f")
    kurs_bank = st.number_input("Bank kurs (rastamojka)", value=12850.56, step=0.01, format="%.2f")
    sertifikat_baza = st.number_input("1 model sertifikat narxi (so'm)", value=8500000.0, step=100.0)

if uploaded_file:
    if "df" not in st.session_state:
        if uploaded_file.name.endswith("csv"):
            df_init = pd.read_csv(uploaded_file)
        else:
            df_init = pd.read_excel(uploaded_file)
        
        df_init.columns = df_init.columns.str.strip()
        
        needed = ["№","Model","Soni","Narxi","Brutto","Netto","Rastamojka","Qo'qon","Samarqand","Xorazm"]
        for col in needed:
            if col not in df_init.columns: df_init[col] = 0.0
            
        st.session_state.df = df_init

    df = st.session_state.df.copy()
    
    # ---------------- HISOB-KITOB (YAXLITLASHSIZ) ----------------
    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    df["Jami netto"] = df["Netto"] * df["Soni"]

    j_brutto = df["Jami brutto"].sum()
    j_narx = df["Jami narxi"].sum()

    df["Yo'l kiro"] = (df["Jami brutto"] * yol_kira / j_brutto) if j_brutto > 0 else 0
    df["Dona yo'l kiro"] = df["Yo'l kiro"] / df["Soni"]

    # Rastamojka aniq hisob (kurs_bank 12850.56 kabi qabul qilinadi)
    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    df["Dona rastamojka"] = df["Rastamojka"] / df["Soni"]
    df["Dona rastamojka $"] = df["Rastamojka $"] / df["Soni"]

    # Sertifikat
    m_soni = df["Model"].nunique()
    j_sert = (sertifikat_baza * m_soni) / kurs_naqd
    df["Sertifikat harajati"] = (df["Jami narxi"] * j_sert / j_narx) if j_narx > 0 else 0
    df["Dona sertifikat harajati"] = df["Sertifikat harajati"] / df["Soni"]

    # Umumiy harajat va Kirim
    df["Harajat"] = df["Yo'l kiro"] + df["Rastamojka $"] + df["Sertifikat harajati"]
    df["Dona harajat"] = df["Harajat"] / df["Soni"]
    df["Kirim"] = df["Narxi"] + df["Dona harajat"]
    df["Jami kirim"] = df["Kirim"] * df["Soni"]

    # Hududlar
    df["Jami Qo'qon"] = df["Qo'qon"] * df["Kirim"]
    df["Jami Samarqand"] = df["Samarqand"] * df["Kirim"]
    df["Jami Xorazm"] = df["Xorazm"] * df["Kirim"]

    columns_order = [
        "№", "Model", "Soni", "Narxi", "Jami narxi", "Brutto", "Jami brutto", 
        "Netto", "Jami netto", "Yo'l kiro", "Dona yo'l kiro", "Rastamojka", 
        "Dona rastamojka", "Rastamojka $", "Dona rastamojka $", "Sertifikat harajati", 
        "Dona sertifikat harajati", "Harajat", "Dona harajat", "Kirim", 
        "Jami kirim", "Qo'qon", "Jami Qo'qon", "Samarqand", "Jami Samarqand", 
        "Xorazm", "Jami Xorazm"
    ]

    # ---------------- JADVAL KO'RINISHI ----------------
    st.info("💡 'Rastamojka' ustuniga aniq son kiriting (masalan: 12850.56).")
    
    updated_df = st.data_editor(
        df[columns_order],
        use_container_width=True,
        hide_index=True,
        column_config={
            # format="%.2f" nuqtadan keyin 2 ta raqamni aniq ko'rsatadi
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%.2f", step=0.01),
        },
        disabled=[c for c in columns_order if c != "Rastamojka"],
        key="single_editor"
    )

    if not updated_df.equals(df[columns_order]):
        st.session_state.df["Rastamojka"] = updated_df["Rastamojka"]
        st.rerun()

    # ---------------- METRIKALAR VA EXCEL ----------------
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    # Metriclarda ham aniqlikni saqlaymiz
    c1.metric("Jami Brutto", f"{j_brutto:,.2f}")
    c2.metric("Modellar", m_soni)
    c3.metric("Jami Sertifikat ($)", f"{j_sert:,.4f}")
    c4.metric("JAMI KIRIM ($)", f"{df['Jami kirim'].sum():,.2f}")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        updated_df.to_excel(writer, index=False, sheet_name="Kirim")
    st.download_button("📥 Excel yuklab olish (Aniq hisob bilan)", output.getvalue(), "lider_hisob.xlsx")

else:
    st.info("Excel fayl yuklang.")
