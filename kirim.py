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
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()

    # Kerakli ustunlarni tekshirish
    required_columns = ["№","Model","Soni","Narxi","Brutto","Netto","Rastamojka","Qo'qon","Samarqand","Xorazm"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0.0

    # 1. ASOSIY JADVAL (FAQAT SHU BITTA EKRANDA TURADI)
    st.subheader("📝 Ma'lumotlarni tahrirlash")
    
    # data_editor natijasini to'g'ridan-to'g'ri df ga olamiz
    df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%d"),
            "Narxi": st.column_config.NumberColumn("Narxi ($)", format="%.2f"),
        },
        # Faqat kerakli ustunlarni tahrirlashga ruxsat (masalan, Rastamojka va Narxi)
        disabled=[col for col in df.columns if col not in ["Rastamojka", "Narxi"]]
    )

    # ---------------- HISOB-KITOB (ORQA FONDA) ----------------
    # Bu hisoblar jadval ko'rinmaydi, lekin Excel va Metrikalar uchun ishlaydi
    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    
    jami_brutto = df["Jami brutto"].sum()
    jami_narx = df["Jami narxi"].sum()
    
    # Yo'l kira
    df["Yo'l kiro"] = (df["Jami brutto"] * yol_kira / jami_brutto) if jami_brutto > 0 else 0
    # Rastamojka $
    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    # Sertifikat
    model_turlari = df["Model"].nunique()
    jami_sertifikat = (sertifikat_baza * model_turlari) / kurs_naqd
    df["Sertifikat harajati"] = (df["Jami narxi"] * jami_sertifikat / jami_narx) if jami_narx > 0 else 0
    
    # Kirim hisobi
    df["Dona harajat"] = (df["Yo'l kiro"] + df["Rastamojka $"] + df["Sertifikat harajati"]) / df["Soni"]
    df["Kirim"] = df["Narxi"] + df["Dona harajat"]
    df["Jami kirim"] = df["Kirim"] * df["Soni"]

    # 2. NATIJALARNI METRIKALARDA KO'RSATAMIZ
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jami Brutto", f"{jami_brutto:,.2f} kg")
    m2.metric("Modellar soni", model_turlari)
    m3.metric("Jami Sertifikat ($)", f"{jami_sertifikat:,.2f}")
    m4.metric("JAMI KIRIM ($)", f"{df['Jami kirim'].sum():,.2f}")

    # 3. EXCELNI TAYYORLASH (HAMMA USTUNLAR BILAN)
    # Bu yerda hamma hisoblangan ustunlarni tartiblab Excelga chiqaramiz
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Hisob-kitob")
    
    st.success("✅ Hisoblash tayyor. Pastdagi tugma orqali hamma ustunlari bor Excelni yuklab oling.")
    
    st.download_button(
        "📥 To'liq hisoblangan Excelni yuklab olish",
        data=output.getvalue(),
        file_name="yuk_hisobi_yakuniy.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Iltimos, Excel faylni yuklang.")
