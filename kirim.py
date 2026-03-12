import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Lider Logistik", layout="wide")

st.title("📦 Yuk Kirimi Hisoblash")

# ---------------- SIDEBAR ----------------

with st.sidebar:
    uploaded_file = st.file_uploader(
        "Excel yoki CSV fayl yuklang",
        type=["xlsx","csv"]
    )

    yol_kira = st.number_input("Jami Yo'l kira ($)", value=1800.0)
    kurs_naqd = st.number_input("Naqd kurs (sertifikat)", value=12900)
    kurs_bank = st.number_input("Bank kurs (rastamojka)", value=12850)
    sertifikat_baza = st.number_input(
        "1 model sertifikat narxi (so'm)",
        value=8500000
    )

# ---------------- FILE LOAD ----------------

if uploaded_file:
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()

# ---------------- KERAKLI USTUNLAR ----------------

    required_columns = [
        "№","Model","Soni","Narxi",
        "Brutto","Netto","Rastamojka",
        "Qo'qon","Samarqand","Xorazm"
    ]

    for col in required_columns:
        if col not in df.columns:
            df[col] = 0.0

# ---------------- INTERAKTIV JADVAL (INPUT) ----------------
# Bu yerda foydalanuvchi Rastamojka ustunini to'ldiradi

    st.subheader("📝 Rastamojka (so'm) qiymatlarini kiriting")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "Rastamojka": st.column_config.NumberColumn(
                "Rastamojka (so'm)",
                help="Har bir model uchun rastamojka summasini so'mda kiriting",
                min_value=0,
                format="%d"
            )
        },
        # Faqat Rastamojka ustunini tahrirlashga ruxsat, qolganlari bloklangan
        disabled=["№","Model","Soni","Narxi","Brutto","Netto","Qo'qon","Samarqand","Xorazm"],
        use_container_width=True,
        hide_index=True
    )

    # Hisob-kitoblar tahrirlangan jadval (edited_df) asosida davom etadi
    df = edited_df.copy()

# ---------------- ASOSIY HISOB (ESKI FORMULALAR) ----------------

    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    df["Jami netto"] = df["Netto"] * df["Soni"]

    jami_brutto = df["Jami brutto"].sum()
    jami_narx = df["Jami narxi"].sum()

# ---------------- YO'L KIRA (ESKI FORMULA) ----------------

    if jami_brutto > 0:
        df["Yo'l kiro"] = df["Jami brutto"] * yol_kira / jami_brutto
    else:
        df["Yo'l kiro"] = 0

    df["Dona yo'l kiro"] = df["Yo'l kiro"] / df["Soni"]

# ---------------- RASTAMOJKA (BANK KURSI BILAN) ----------------

    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    df["Dona rastamojka"] = df["Rastamojka"] / df["Soni"]
    df["Dona rastamojka $"] = df["Rastamojka $"] / df["Soni"]

# ---------------- SERTIFIKAT ----------------

    model_turlari = df["Model"].nunique()
    jami_sertifikat = (sertifikat_baza * model_turlari) / kurs_naqd

    if jami_narx > 0:
        df["Sertifikat harajati"] = (
            df["Jami narxi"] * jami_sertifikat / jami_narx
        )
    else:
        df["Sertifikat harajati"] = 0

    df["Dona sertifikat harajati"] = (
        df["Sertifikat harajati"] / df["Soni"]
    )

# ---------------- UMUMIY HARAJAT ----------------

    df["Harajat"] = (
        df["Yo'l kiro"]
        + df["Rastamojka $"]
        + df["Sertifikat harajati"]
    )

    df["Dona harajat"] = df["Harajat"] / df["Soni"]

# ---------------- KIRIM ----------------

    df["Kirim"] = df["Narxi"] + df["Dona harajat"]
    df["Jami kirim"] = df["Kirim"] * df["Soni"]

# ---------------- HUDUDLAR (HUDUDLAR HISOBI HAM JOYIDA) ----------------

    df["Jami Qo'qon"] = df["Qo'qon"] * df["Kirim"]
    df["Jami Samarqand"] = df["Samarqand"] * df["Kirim"]
    df["Jami Xorazm"] = df["Xorazm"] * df["Kirim"]

# ---------------- QO'SHIMCHA USTUNLAR ----------------

    extra_cols = ["Chiqim A", "Chiqim B,C", "Darian narxi", "Ustama"]

    for col in extra_cols:
        if col not in df.columns:
            df[col] = ""

# ---------------- USTUNLAR TARTIBI (HAMMASI SAQLANDI) ----------------

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

    # Yetishmayotgan ustunlarni bo'sh qoldirish
    for col in columns_order:
        if col not in df.columns:
            df[col] = ""

    final_df = df[columns_order]

# ---------------- METRICS ----------------

    st.divider()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Jami brutto", f"{jami_brutto:,.2f}")
    c2.metric("Model soni", model_turlari)
    c3.metric("Jami sertifikat $", f"{jami_sertifikat:,.2f}")
    c4.metric("Jami kirim $", f"{df['Jami kirim'].sum():,.2f}")

# ---------------- YAKUNIY JADVAL ----------------

    st.subheader("📊 Hisoblangan natijalar")
    st.dataframe(
        final_df.style.format(precision=2),
        use_container_width=True
    )

# ---------------- EXCEL EXPORT ----------------

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Kirim")

    st.download_button(
        "📥 Excel yuklab olish",
        data=output.getvalue(),
        file_name="yuk_kirimi_hisoblandi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Excel fayl yuklang.")
