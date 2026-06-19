import streamlit as st
import pandas as pd
import os

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Manajemen Material & SN IKR", 
    layout="wide", 
    page_icon="⚡"
)

# NAMA FILE (WAJIB SAMA PERSIS DENGAN YANG DI UPLOAD KE GITHUB)
EXCEL_FILE = "MATERIAL IKR [ KEBUTUHAN WO HARIAN ].xlsx"
MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"

# Fungsi loading data master SN
@st.cache_data
def load_master_sn():
    if os.path.exists(MASTER_SN_FILE):
        try:
            # Membaca file CSV Master SN
            df = pd.read_csv(MASTER_SN_FILE)
            # Bersihkan spasi gaib di nama kolom
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.error(f"❌ Gagal membaca file CSV Master SN: {e}")
            return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])
    return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])

# Fungsi loading sheet Excel
@st.cache_data
def load_excel_sheet(sheet_name):
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, engine='openpyxl')
            return df
        except Exception as e:
            return None
    return None

# --- LOAD DATA ---
df_master = load_master_sn()
df_device = load_excel_sheet("Stock Device")
df_precon = load_excel_sheet("Stock PRECON")

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("Sistem Kontrol IKR")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "PILIH MENU APLIKASI:",
    ["📊 Dashboard Utama", "🔍 Scan & Lihat Master SN", "📦 Stok Gudang", "👨‍🔧 Data Harian Teknisi"]
)

# ==================== 1. DASHBOARD UTAMA ====================
if menu == "📊 Dashboard Utama":
    st.title("📊 Dashboard Utama")
    
    total_sn = len(df_master)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Master SN Terbaca", value=f"{int(total_sn)} Item")
        
    st.markdown("### 📌 Status Sinkronisasi File di GitHub")
    if os.path.exists(MASTER_SN_FILE):
        st.success(f"✅ Master SN Terkoneksi Sempurna ({MASTER_SN_FILE})")
    else:
        st.error(f"❌ File '{MASTER_SN_FILE}' tidak ditemukan! Periksa kembali nama file yang kamu upload di GitHub.")

# ==================== 2. SCAN & LIHAT MASTER SN ====================
elif menu == "🔍 Scan & Lihat Master SN":
    st.title("🔍 Pusat Data & Validasi Master SN")
    
    # Bagian 1: Fitur Cari/Scan
    st.subheader("⚙️ Scan / Cari SN Spesifik")
    input_sn = st.text_input("👉 SCAN BARCODE ATAU KETIK NOMOR SN:", placeholder="Contoh: ZTEGDD2B1636...").strip()
    
    if input_sn:
        if 'SN' in df_master.columns:
            hasil = df_master[df_master['SN'].astype(str).str.lower() == input_sn.lower()]
            if not hasil.empty:
                st.success("🎉 NOMOR SN TERDAFTAR DI MASTER!")
                st.dataframe(hasil, use_container_width=True)
            else:
                st.error(f"⚠️ Nomor SN '{input_sn}' TIDAK DITEMUKAN!")
        else:
            st.error("❌ Kolom bernama 'SN' tidak ditemukan di file CSV kamu.")

    st.markdown("---")
    
    # Bagian 2: Menampilkan Seluruh Isi Tabel CSV
    st.subheader("📋 Semua Daftar Master SN Terdaftar")
    st.write(f"Menampilkan total **{len(df_master)}** baris data yang ada di dalam file CSV kamu:")
    
    if not df_master.empty:
        st.dataframe(df_master, use_container_width=True)
    else:
        st.info("Tabel kosong karena file CSV belum terbaca. Pastikan status di Dashboard sudah berwarna hijau ya!")

# ==================== 3. STOK GUDANG ====================
elif menu == "📦 Stok Gudang":
    st.title("📦 Data Stok Gudang")
    t1, t2 = st.tabs(["📟 Device", "🧵 Kabel PRECON"])
    with t1:
        if df_device is not None: st.dataframe(df_device, use_container_width=True)
        else: st.info("File Excel harian belum di-upload ke GitHub.")
    with t2:
        if df_precon is not None: st.dataframe(df_precon, use_container_width=True)
        else: st.info("File Excel harian belum di-upload ke GitHub.")

# ==================== 4. DATA HARIAN TEKNISI ====================
elif menu == "👨‍🔧 Data Harian Teknisi":
    st.title("👨‍🔧 Data Teknisi")
    daftar_teknisi = ["PUTRA-SONY", "RIYAN-RIYADI", "NADI-PARI", "ARIF-YASRIL"]
    pilihan = st.selectbox("Pilih Tim:", daftar_teknisi)
    df_tek = load_excel_sheet(pilihan)
    if df_tek is not None: st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
    else: st.info("Data sheet teknisi tidak ditemukan.")
