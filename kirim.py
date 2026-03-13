import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Lider Logistik", layout="wide")
st.title("📦 Yuk Kirimi Hisoblash")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    uploaded_file = st.file_uploader("Excel yoki CSV fayl yuklang", type=["xlsx","csv"])
    yol_kira = st.number_input("Jami Yo'l kira ($)", value=1800.0)
    kurs_naqd = st.number_input("Naqd kurs (sertifikat)", value=12900)
    kurs_bank = st.number_input("Bank kurs (rastamojka)", value=12850)
    sertifikat_baza = st.number_input("1 model sertifikat narxi (so'm)", value=8500000)

if uploaded_file:
    # 1. Ma'lumotni session_state'da saqlash (qayta yuklanganda yo'qolmasligi uchun)
    if "df" not in st.session_state:
        if uploaded_file.name.endswith("csv"):
            df_init = pd.read_csv(uploaded_file)
        else:
            df_init = pd.read_excel(uploaded_file)
        
        df_init.columns = df_init.columns.str.strip()
        
        # Kerakli ustunlar
        needed = ["№","Model","Soni","Narxi","Brutto","Netto","Rastamojka","Qo'qon","Samarqand","Xorazm"]
        for col in needed:
            if col not in df_init.columns: df_init[col] = 0.0
            
        st.session_state.df = df_init

    # 2. HISOB-KITOB FORMULALARI (Jadvaldan oldin hisoblanadi)
    df = st.session_state.df.copy()
    
    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    df["Jami netto"] = df["Netto"] * df["Soni"]

    j_brutto = df["Jami brutto"].sum()
    j_narx = df["Jami narxi"].sum()

    df["Yo'l kiro"] = (df["Jami brutto"] * yol_kira / j_brutto) if j_brutto > 0 else 0
    df["Dona yo'l kiro"] = df["Yo'l kiro"] / df["Soni"]

    # Siz aytgan Rastamojka ustunlari
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

    # Ustunlar tartibi (31 ta ustun)
    columns_order = [
        "№", "Model", "Soni", "Narxi", "Jami narxi", "Brutto", "Jami brutto", 
        "Netto", "Jami netto", "Yo'l kiro", "Dona yo'l kiro", "Rastamojka", 
        "Dona rastamojka", "Rastamojka $", "Dona rastamojka $", "Sertifikat harajati", 
        "Dona sertifikat harajati", "Harajat", "Dona harajat", "Kirim", 
        "Jami kirim", "Qo'qon", "Jami Qo'qon", "Samarqand", "Jami Samarqand", 
        "Xorazm", "Jami Xorazm"
    ]
    for col in columns_order:
        if col not in df.columns: df[col] = 0

    # 3. FAQAT BITTA JADVAL (Input va Output bittada)
    st.info("💡 'Rastamojka' ustunini tahrirlang, qolgan hamma ustunlar o'sha zahoti o'zgaradi.")
    
    updated_df = st.data_editor(
        df[columns_order],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%d"),
        },
        disabled=[c for c in columns_order if c != "Rastamojka"],
        key="single_editor"
    )

    # Agar ma'lumot o'zgargan bo'lsa, session_state'ni yangilaymiz
    if not updated_df.equals(df[columns_order]):
        st.session_state.df["Rastamojka"] = updated_df["Rastamojka"]
        st.rerun()

    # 4. METRIKALAR (Jadval tagida)
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami Brutto", f"{j_brutto:,.2f}")
    c2.metric("Modellar", m_soni)
    c3.metric("Sertifikat ($)", f"{j_sert:,.2f}")
    c4.metric("JAMI KIRIM ($)", f"{df['Jami kirim'].sum():,.2f}")

    # 5. EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        updated_df.to_excel(writer, index=False, sheet_name="Kirim")
    st.download_button("📥 Excel yuklab olish", output.getvalue(), "hisob.xlsx")

else:
    st.info("Excel fayl yuklang.")
