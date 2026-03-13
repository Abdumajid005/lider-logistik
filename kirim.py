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

# ---------------- SESSION STATE (Ma'lumotlarni saqlash uchun) ----------------
if uploaded_file:
    if "df_data" not in st.session_state:
        if uploaded_file.name.endswith("csv"):
            df_init = pd.read_csv(uploaded_file)
        else:
            df_init = pd.read_excel(uploaded_file)
        
        df_init.columns = df_init.columns.str.strip()
        
        # Kerakli ustunlar yo'q bo'lsa yaratish
        required_cols = ["№","Model","Soni","Narxi","Brutto","Netto","Rastamojka","Qo'qon","Samarqand","Xorazm"]
        for col in required_cols:
            if col not in df_init.columns:
                df_init[col] = 0.0
        
        st.session_state.df_data = df_init

    # 1. FOYDALANUVCHI TAHRIRLAYDIGAN JADVAL
    st.info("💡 'Rastamojka' ustunini tahrirlang, qolganlari avtomat hisoblanadi.")
    
    edited_df = st.data_editor(
        st.session_state.df_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%d"),
        },
        disabled=[col for col in st.session_state.df_data.columns if col != "Rastamojka"]
    )
    
    # Tahrirlangan ma'lumotni saqlaymiz
    df = edited_df.copy()

    # ---------------- BARCHA FORMULALAR (ESKI TARTIBDA) ----------------
    
    # Asosiy hisoblar
    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    df["Jami netto"] = df["Netto"] * df["Soni"]

    jami_brutto = df["Jami brutto"].sum()
    jami_narx = df["Jami narxi"].sum()

    # Yo'l kira
    if jami_brutto > 0:
        df["Yo'l kiro"] = df["Jami brutto"] * yol_kira / jami_brutto
    else:
        df["Yo'l kiro"] = 0
    df["Dona yo'l kiro"] = df["Yo'l kiro"] / df["Soni"]

    # Rastamojka (Bank kursi bilan)
    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    df["Dona rastamojka"] = df["Rastamojka"] / df["Soni"]
    df["Dona rastamojka $"] = df["Rastamojka $"] / df["Soni"]

    # Sertifikat
    model_turlari = df["Model"].nunique()
    jami_sertifikat_dollarda = (sertifikat_baza * model_turlari) / kurs_naqd

    if jami_narx > 0:
        df["Sertifikat harajati"] = (df["Jami narxi"] * jami_sertifikat_dollarda / jami_narx)
    else:
        df["Sertifikat harajati"] = 0
    df["Dona sertifikat harajati"] = df["Sertifikat harajati"] / df["Soni"]

    # Umumiy harajat
    df["Harajat"] = df["Yo'l kiro"] + df["Rastamojka $"] + df["Sertifikat harajati"]
    df["Dona harajat"] = df["Harajat"] / df["Soni"]

    # Kirim
    df["Kirim"] = df["Narxi"] + df["Dona harajat"]
    df["Jami kirim"] = df["Kirim"] * df["Soni"]

    # Hududlar
    df["Jami Qo'qon"] = df["Qo'qon"] * df["Kirim"]
    df["Jami Samarqand"] = df["Samarqand"] * df["Kirim"]
    df["Jami Xorazm"] = df["Xorazm"] * df["Kirim"]

    # Qo'shimcha ustunlar (Chiqim A, B, C...)
    extra_cols = ["Chiqim A", "Chiqim B,C", "Darian narxi", "Ustama"]
    for col in extra_cols:
        if col not in df.columns:
            df[col] = ""

    # ---------------- USTUNLAR TARTIBI (SIZ AYTGAN TARTIB) ----------------
    columns_order = [
        "№", "Model", "Soni", "Narxi", "Jami narxi", 
        "Brutto", "Jami brutto", "Netto", "Jami netto", 
        "Yo'l kiro", "Dona yo'l kiro", "Rastamojka", 
        "Dona rastamojka", "Rastamojka $", "Dona rastamojka $", 
        "Sertifikat harajati", "Dona sertifikat harajati", 
        "Harajat", "Dona harajat", "Kirim", "Jami kirim", 
        "Chiqim A", "Chiqim B,C", "Darian narxi", "Ustama", 
        "Qo'qon", "Jami Qo'qon", "Samarqand", "Jami Samarqand", 
        "Xorazm", "Jami Xorazm"
    ]

    # Yakuniy jadvalni tayyorlash
    for col in columns_order:
        if col not in df.columns:
            df[col] = ""
            
    final_df = df[columns_order]

    # ---------------- NATIJA VA EXPORT ----------------
    
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami Brutto", f"{jami_brutto:,.2f}")
    c2.metric("Modellar soni", model_turlari)
    c3.metric("Jami Sertifikat ($)", f"{jami_sertifikat_dollarda:,.2f}")
    c4.metric("Jami Kirim ($)", f"{df['Jami kirim'].sum():,.2f}")

    st.subheader("📊 Hisob-kitob natijalari (31 ta ustun)")
    st.dataframe(final_df.style.format(precision=2, subset=final_df.select_dtypes(include='number').columns), use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Kirim")

    st.download_button(
        "📥 Excel yuklab olish",
        data=output.getvalue(),
        file_name="lider_logistik_yakuniy.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Excel fayl yuklang.")
