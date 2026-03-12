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

# ---------------- FILE LOAD & CALCULATION ----------------
if uploaded_file:
    if uploaded_file.name.endswith("csv"):
        original_df = pd.read_csv(uploaded_file)
    else:
        original_df = pd.read_excel(uploaded_file)

    original_df.columns = original_df.columns.str.strip()

    # Kerakli ustunlar bazada bormi tekshirish
    required_columns = ["№","Model","Soni","Narxi","Brutto","Netto","Rastamojka","Qo'qon","Samarqand","Xorazm"]
    for col in required_columns:
        if col not in original_df.columns:
            original_df[col] = 0.0

    # --- JADVALNI CHIQARISH VA TAHRIRLASH ---
    st.info("💡 'Rastamojka' ustunini to'ldiring, qolgan ustunlar avtomat hisoblanadi.")

    # 1. Avval foydalanuvchi kiritgan qiymatlarni qabul qilamiz
    edited_df = st.data_editor(
        original_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%d"),
        },
        disabled=[c for c in original_df.columns if c != "Rastamojka"]
    )

    # 2. ENDI FAQAT SHU BITTA JADVAL ASOSIDA HAMMA FORMULALARNI HISOBLAYMIZ
    df = edited_df.copy()

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

    # Rastamojka $
    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    df["Dona rastamojka"] = df["Rastamojka"] / df["Soni"]
    df["Dona rastamojka $"] = df["Rastamojka $"] / df["Soni"]

    # Sertifikat
    model_turlari = df["Model"].nunique()
    jami_sertifikat = (sertifikat_baza * model_turlari) / kurs_naqd
    if jami_narx > 0:
        df["Sertifikat harajati"] = (df["Jami narxi"] * jami_sertifikat / jami_narx)
    else:
        df["Sertifikat harajati"] = 0
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

    # 3. METRIKALAR (Jadval tagida yangilanib turadi)
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami Brutto", f"{jami_brutto:,.2f}")
    c2.metric("Modellar", model_turlari)
    c3.metric("Sertifikat ($)", f"{jami_sertifikat:,.2f}")
    c4.metric("Jami Kirim ($)", f"{df['Jami kirim'].sum():,.2f}")

    # 4. FAQAT BITTA JADVAL KO'RINISHI UCHUN NATIJANI QAYTA CHIQARAMIZ
    # Lekin bu yerda 'final_df' tartibini beramiz
    columns_order = [
        "№", "Model", "Soni", "Narxi", "Jami narxi", 
        "Brutto", "Jami brutto", "Yo'l kiro", "Dona yo'l kiro", 
        "Rastamojka", "Rastamojka $", "Dona rastamojka $", 
        "Sertifikat harajati", "Harajat", "Dona harajat", 
        "Kirim", "Jami kirim", "Qo'qon", "Jami Qo'qon", 
        "Samarqand", "Jami Samarqand", "Xorazm", "Jami Xorazm"
    ]
    
    # Mavjud bo'lmagan ustunlarni to'ldirish
    for col in columns_order:
        if col not in df.columns: df[col] = 0

    st.subheader("📊 Hisoblangan Yakuniy Jadval")
    # BU YERDA FAQAT NATIJANI KO'RSATAMIZ (BITTA JADVAL BO'LISHI UCHUN)
    st.dataframe(df[columns_order].style.format(precision=2), use_container_width=True)

    # Excelga yuklash
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df[columns_order].to_excel(writer, index=False, sheet_name="Kirim")
    
    st.download_button(
        "📥 Tayyor Excelni yuklab olish",
        data=output.getvalue(),
        file_name="lider_hisob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Iltimos, Excel fayl yuklang.")
