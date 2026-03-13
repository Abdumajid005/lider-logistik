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

# ---------------- HISOB-KITOB VA JADVAL ----------------
if uploaded_file:
    # Faylni yuklash
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()

    # Kerakli boshlang'ich ustunlar borligini tekshirish
    required_cols = ["№", "Model", "Soni", "Narxi", "Brutto", "Netto", "Rastamojka", "Qo'qon", "Samarqand", "Xorazm"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0

    # 1. ASOSIY HISOB-KITOB FORMULALARI
    # (Dastlabki hisoblar tahrirlashdan oldin bajariladi)
    df["Jami narxi"] = df["Narxi"] * df["Soni"]
    df["Jami brutto"] = df["Brutto"] * df["Soni"]
    df["Jami netto"] = df["Netto"] * df["Soni"]

    jami_brutto = df["Jami brutto"].sum()
    jami_narx = df["Jami narxi"].sum()

    # Yo'l kira
    df["Yo'l kiro"] = (df["Jami brutto"] * yol_kira / jami_brutto) if jami_brutto > 0 else 0
    df["Dona yo'l kiro"] = df["Yo'l kiro"] / df["Soni"]

    # Sertifikat
    model_turlari = df["Model"].nunique()
    jami_sertifikat_dollarda = (sertifikat_baza * model_turlari) / kurs_naqd
    df["Sertifikat harajati"] = (df["Jami narxi"] * jami_sertifikat_dollarda / jami_narx) if jami_narx > 0 else 0
    df["Dona sertifikat harajati"] = df["Sertifikat harajati"] / df["Soni"]

    # Rastamojka $ va boshqa dinamik ustunlar (dastlab 0 yoki hisoblangan)
    df["Rastamojka $"] = df["Rastamojka"] / kurs_bank
    df["Dona rastamojka $"] = df["Rastamojka $"] / df["Soni"]
    df["Harajat"] = df["Yo'l kiro"] + df["Rastamojka $"] + df["Sertifikat harajati"]
    df["Dona harajat"] = df["Harajat"] / df["Soni"]
    df["Kirim"] = df["Narxi"] + df["Dona harajat"]
    df["Jami kirim"] = df["Kirim"] * df["Soni"]

    # Hududlar
    df["Jami Qo'qon"] = df["Qo'qon"] * df["Kirim"]
    df["Jami Samarqand"] = df["Samarqand"] * df["Kirim"]
    df["Jami Xorazm"] = df["Xorazm"] * df["Kirim"]

    # Qo'shimcha ustunlar
    for col in ["Chiqim A", "Chiqim B,C", "Darian narxi", "Ustama"]:
        if col not in df.columns: df[col] = ""

    # 2. USTUNLAR TARTIBI
    columns_order = [
        "№", "Model", "Soni", "Narxi", "Jami narxi", "Brutto", "Jami brutto", 
        "Netto", "Jami netto", "Yo'l kiro", "Dona yo'l kiro", "Rastamojka", 
        "Rastamojka $", "Dona rastamojka $", "Sertifikat harajati", 
        "Dona sertifikat harajati", "Harajat", "Dona harajat", "Kirim", 
        "Jami kirim", "Chiqim A", "Chiqim B,C", "Darian narxi", "Ustama", 
        "Qo'qon", "Jami Qo'qon", "Samarqand", "Jami Samarqand", "Xorazm", "Jami Xorazm"
    ]

    # 3. FAQAT BITTA TAHRIRLANADIGAN JADVAL (31 ta ustun bilan)
    st.subheader("📊 Yakuniy Hisob-kitob Jadvali")
    st.info("💡 'Rastamojka' ustuniga so'mda qiymat kiriting, qolgan hamma ustunlar o'zi hisoblanadi.")

    # Tahrirlanadigan asosiy jadval
    final_df = st.data_editor(
        df[columns_order],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rastamojka": st.column_config.NumberColumn("Rastamojka (so'm)", format="%d"),
            # Boshqa raqamli ustunlarni chiroyli formatlash
            **{c: st.column_config.NumberColumn(format="%.2f") for c in columns_order if c != "Rastamojka" and c != "Model"}
        },
        # Faqat Rastamojka ustunini ochiq qoldiramiz, qolganlari BLOCK
        disabled=[c for c in columns_order if c != "Rastamojka"]
    )

    # 4. METRIKALAR (Jadval ostida)
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami Brutto", f"{jami_brutto:,.2f}")
    c2.metric("Modellar soni", model_turlari)
    c3.metric("Jami Sertifikat ($)", f"{jami_sertifikat_dollarda:,.2f}")
    c4.metric("JAMI KIRIM ($)", f"{final_df['Jami kirim'].sum():,.2f}")

    # 5. EXCEL EXPORT
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Kirim")

    st.download_button(
        "📥 Excel yuklab olish",
        data=output.getvalue(),
        file_name="lider_logistik_hisob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Iltimos, Excel fayl yuklang.")
