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

# ---------------- HISOB-KITOB FUNKSIYASI ----------------
def calculate_all(df):
    """Barcha formulalarni bitta joyda hisoblash"""
    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    df["Jami netto"] = df["Netto"] * df["Soni"]

    total_brutto = df["Jami brutto"].sum()
    total_price = df["Jami narxi"].sum()

    # Yo'l kira
    df["Yo'l kiro"] = (df["Jami brutto"] * yol_kira / total_brutto) if total_brutto > 0 else 0
    df["Dona yo'l kiro"] = df["Yo'l kiro"] / df["Soni"]

    # Rastamojka (Siz aytgan ustunlar)
    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    df["Dona rastamojka"] = df["Rastamojka"] / df["Soni"]
    df["Dona rastamojka $"] = df["Rastamojka $"] / df["Soni"]

    # Sertifikat
    model_count = df["Model"].nunique()
    cert_total_usd = (sertifikat_baza * model_count) / kurs_naqd
    df["Sertifikat harajati"] = (df["Jami narxi"] * cert_total_usd / total_price) if total_price > 0 else 0
    df["Dona sertifikat harajati"] = df["Sertifikat harajati"] / df["Soni"]

    # Kirim va Harajat
    df["Harajat"] = df["Yo'l kiro"] + df["Rastamojka $"] + df["Sertifikat harajati"]
    df["Dona harajat"] = df["Harajat"] / df["Soni"]
    df["Kirim"] = df["Narxi"] + df["Dona harajat"]
    df["Jami kirim"] = df["Kirim"] * df["Soni"]

    # Hududlar
    df["Jami Qo'qon"] = df["Qo'qon"] * df["Kirim"]
    df["Jami Samarqand"] = df["Samarqand"] * df["Kirim"]
    df["Jami Xorazm"] = df["Xorazm"] * df["Kirim"]
    
    return df, total_brutto, cert_total_usd

# ---------------- MAIN LOGIC ----------------
if uploaded_file:
    # Faylni bir marta o'qib olish
    if "raw_df" not in st.session_state:
        if uploaded_file.name.endswith("csv"):
            df_init = pd.read_csv(uploaded_file)
        else:
            df_init = pd.read_excel(uploaded_file)
        
        df_init.columns = df_init.columns.str.strip()
        # Rastamojka ustuni bo'lmasa yaratish
        if "Rastamojka" not in df_init.columns:
            df_init["Rastamojka"] = 0.0
        
        st.session_state.raw_df = df_init

    # 1. TAHRIRLASH JADVALINI KO'RSATISH
    st.info("💡 'Rastamojka' ustuniga so'mda qiymat kiriting va Enter bosing.")
    
    # Ma'lumotlarni tahrirlash (faqat Rastamojka ustuni ochiq)
    edited_df = st.data_editor(
        st.session_state.raw_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%d"),
        },
        disabled=[c for c in st.session_state.raw_df.columns if c != "Rastamojka"],
        key="main_editor"
    )

    # 2. HAMMA NARSANI HISOBLASH
    # Tahrirlangan df ni funksiyaga yuboramiz
    final_df, j_brutto, j_sert = calculate_all(edited_df)

    # 3. METRIKALAR
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami Brutto", f"{j_brutto:,.2f}")
    c2.metric("Modellar soni", final_df["Model"].nunique())
    c3.metric("Jami Sertifikat ($)", f"{j_sert:,.2f}")
    c4.metric("JAMI KIRIM ($)", f"{final_df['Jami kirim'].sum():,.2f}")

    # 4. NATIJAVIY JADVAL (31 ta ustun tartibida)
    columns_order = [
        "№", "Model", "Soni", "Narxi", "Jami narxi", "Brutto", "Jami brutto", 
        "Netto", "Jami netto", "Yo'l kiro", "Dona yo'l kiro", "Rastamojka", 
        "Dona rastamojka", "Rastamojka $", "Dona rastamojka $", "Sertifikat harajati", 
        "Dona sertifikat harajati", "Harajat", "Dona harajat", "Kirim", 
        "Jami kirim", "Qo'qon", "Jami Qo'qon", "Samarqand", "Jami Samarqand", 
        "Xorazm", "Jami Xorazm"
    ]

    # Ustunlar borligini tekshirish
    for col in columns_order:
        if col not in final_df.columns: final_df[col] = 0

    st.subheader("📊 Hisob-kitob natijalari")
    st.dataframe(final_df[columns_order].style.format(precision=2), use_container_width=True)

    # 5. EXCEL EXPORT
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df[columns_order].to_excel(writer, index=False, sheet_name="Kirim")

    st.download_button(
        "📥 Tayyor Excelni yuklab olish",
        data=output.getvalue(),
        file_name="lider_logistik_hisob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Iltimos, Excel fayl yuklang.")
