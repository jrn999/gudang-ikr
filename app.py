import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
from github import Github
import io

# Konfigurasi halaman utama
st.set_page_config(page_title="Sistem Logistik IKR Metech", layout="wide", page_icon="⚡")

# --- CUSTOM CSS UNTUK TAMPILAN LEBIH MODERN ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    h1 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Sistem Logistik IKR Metech")

# --- AMBIL KREDENSIAL GITHUB ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = st.secrets.get("GITHUB_REPO", "")

# --- FUNGSI LOAD DATA (LOGIKA SAMA, TIDAK DIUBAH) ---
@st.cache_data
def load_master_sn(nama_file):
    if nama_file and os.path.exists(nama_file):
        try:
            df = pd.read_csv(nama_file)
            df.columns = df.columns.str.strip()
            return df
        except:
            return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])
    return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])

# --- INISIALISASI DATA ---
MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv" # Default fallback
df_master = load_master_sn(MASTER_SN_FILE)

# --- SINKRONISASI FUNGSI ---
def load_atau_buat_file_github(nama_file, df_default):
    if not GITHUB_TOKEN or not REPO_NAME: return df_default
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        try:
            contents = repo.get_contents(nama_file, ref="data-log")
            return pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')))
        except:
            return df_default
    except: return df_default

def simpan_file_ke_github(nama_file, df, pesan_commit="Auto-Update"):
    if not GITHUB_TOKEN or not REPO_NAME: return
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        csv_string = df.to_csv(index=False)
        contents = repo.get_contents(nama_file, ref="data-log")
        repo.update_file(nama_file, f"{pesan_commit} {datetime.now().strftime('%Y-%m-%d %H:%M')}", csv_string, contents.sha, branch="data-log")
    except: pass

# --- SESSION STATE ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = load_atau_buat_file_github("log_harian.csv", pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong']))

# --- NAVIGATION MENU ---
menu_options = {
    "pagi": "✍️ Scan & Input Pagi",
    "sore": "📝 Laporan Sore",
    "bos": "📊 Laporan Eksekutif",
    "gudang": "📉 Stok Gudang",
    "teknisi": "👨‍🔧 Histori Teknisi",
    "pengaturan": "⚙️ Pengaturan"
}

pilihan_menu = st.sidebar.radio("PILIH HALAMAN:", options=list(menu_options.keys()), format_func=lambda x: menu_options[x])

# ==================== MENU 1: PAGI ====================
if pilihan_menu == "pagi":
    st.subheader("✍️ Input Material Pagi")
    with st.container(border=True): # Menggunakan container agar rapi
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🧵 Input Kabel")
            st.selectbox("Pilih Tim:", ["PUTRA-SONY"], key="tek_kabel")
            st.selectbox("Jenis Kabel:", ["DTFIBER - 75MTR"], key="pilihan_kabel")
            st.number_input("Jumlah (Roll):", 1, key="jumlah_roll")
            if st.button("➕ Simpan Kabel", use_container_width=True, type="primary"):
                st.toast("Tersimpan!")
        with col2:
            st.markdown("#### 📟 Scan Device")
            st.text_input("Scan SN:", placeholder="Tembak barcode...", key="scan_sn_key")
            st.info("Status: Menunggu Scan")

# ==================== MENU 2: SORE ====================
elif pilihan_menu == "sore":
    st.subheader("📝 Laporan Hasil Sore")
    with st.container(border=True):
        st.write("Daftar pekerjaan hari ini:")
        if not st.session_state.log_scan_harian.empty:
            st.dataframe(st.session_state.log_scan_harian, use_container_width=True)
        else:
            st.warning("Belum ada data.")

# ==================== MENU 3: BOS ====================
elif pilihan_menu == "bos":
    st.subheader("📊 Laporan Eksekutif")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Keluar", "0")
    col2.metric("Terpasang", "0")
    col3.metric("Rasio", "0%")
    st.markdown("---")
    st.dataframe(st.session_state.log_scan_harian, use_container_width=True)

# ==================== MENU 4: GUDANG ====================
elif pilihan_menu == "gudang":
    st.subheader("📉 Stok Gudang")
    t1, t2 = st.tabs(["📟 Stock Device", "🧵 Stock PRECON"])
    with t1:
        with st.container(border=True):
            st.write("Data Device:")
    with t2:
        with st.container(border=True):
            st.write("Data Kabel:")
