import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

st.title("⚡ Sistem Logistik IKR Metech")

# =========================================================
# 🔍 FITUR DETEKTIF: MENAMPILKAN SEMUA FILE DI GITHUB KAMU
# =========================================================
st.markdown("### 🕵️‍♂️ Fitur Detektif: File yang Terbaca di GitHub Kamu")
with st.expander("👉 KLIK DI SINI UNTUK LIHAT DAFTAR FILE KAMU", expanded=True):
    semua_file = os.listdir('.')
    # Filter hanya file excel dan csv biar gak pusing lihatnya
    file_gudang = [f for f in semua_file if f.endswith('.xlsx') or f.endswith('.csv')]
    
    if file_gudang:
        st.info("Berikut adalah nama-nama file asli yang ada di GitHub kamu saat ini. Tolong COPAS atau FOTOIN daftar ini ke saya ya:")
        for nama_file in file_gudang:
            st.markdown(f"- `{nama_file}`")
    else:
        st.warning("Waduh! Gak ada file Excel (.xlsx) atau CSV (.csv) sama sekali di GitHub kamu.")

st.markdown("---")

# --- PROSES PEMBACAAN FILE (OTOMATIS MENCARI YANG COCOK) ---
# Mencari file master SN secara otomatis
MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"
for f in semua_file:
    if "MASTER_SN" in f:
        MASTER_SN_FILE = f

# Mencari file Excel Utama secara otomatis
EXCEL_FILE = "MATERIAL IKR [ KEBUTUHAN WO HARIAN ].xlsx"
for f in semua_file:
    if "MATERIAL IKR" in f and f.endswith('.xlsx'):
        EXCEL_FILE = f

# --- DEKLARASI SESSION STATE ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = pd.DataFrame(
        columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan']
    )
if 'pesan_sukses' not in st.session_state:
    st.session_state.pesan_sukses = ""

# Fungsi loading data master SN (CSV)
@st.cache_data
def load_master_sn():
    if os.path.exists(MASTER_SN_FILE):
        try:
            df = pd.read_csv(MASTER_SN_FILE)
            df.columns = df.columns.str.strip()
            return df
        except:
            return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])
    return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])

# Fungsi loading sheet dari Excel Asli (.xlsx)
@st.cache_data
def load_excel_sheet(sheet_name):
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, engine='openpyxl')
            df.columns = df.columns.str.strip()
            return df
        except:
            return None
    return None

# --- LOAD DATA ---
df_master = load_master_sn()
df_device = load_excel_sheet("Stock Device")
df_precon = load_excel_sheet("Stock PRECON")

# --- PROSES MEMBUAT DAFTAR KABEL OTOMATIS ---
DAFTAR_KABEL_OTOMATIS = []
if df_precon is not None and 'Description' in df_precon.columns:
    list_kabel = df_precon['Description'].dropna().astype(str).tolist()
    DAFTAR_KABEL_OTOMATIS = [kabel.strip() for kabel in list_kabel if "CABLE" in kabel or "MTR" in kabel]

if not DAFTAR_KABEL_OTOMATIS:
    DAFTAR_KABEL_OTOMATIS = [
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 125MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 175MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 225MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 300MTR"
    ]

DAFTAR_TEKNISI = ["PUTRA-SONY", "RIYAN-RIYADI", "NADI-PARI", "ARIF-YASRIL", "NOVANS-GOBY", "PERI-ROBIN", "TEDI-DODI", "REFKY-DODI", "RAHMAN-AGUS", "IDDO-NAUFAL"]

def proses_scan_sn():
    sn_value = st.session_state.scan_sn_key.strip()
    if sn_value:
        pencarian = df_master[df_master['SN'].astype(str).str.lower() == sn_value.lower()]
        nama_barang = pencarian.iloc[0].get('Nama_Barang', 'Device Terdaftar') if not pencarian.empty else "ONT/STB (Manual/Tidak di Master)"
        
        new_row = {
            'Waktu Scan': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Nama Teknisi': st.session_state.tek_device, 'Serial Number (SN)': sn_value,
            'Nama Barang': nama_barang, 'Kabel Precon': "-", 'No WO / Keterangan': st.session_state.wo_device if st.session_state.wo_device else "-"
        }
        st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' tersimpan!"
        st.session_state.scan_sn_key = ""

# --- SIDEBAR NAVIGASI ---
menu = st.sidebar.radio("PILIH MENU APLIKASI:", ["✍️ Input & Scan Harian Teknisi", "🔍 Lihat & Cari Master SN", "📦 Stok Gudang", "👨‍🔧 Histori Excel Teknisi"])

# ==================== MENU 1: INPUT HARIAN ====================
if menu == "✍️ Input & Scan Harian Teknisi":
    if st.session_state.pesan_sukses:
        st.success(st.session_state.pesan_sukses)
        st.session_state.pesan_sukses = ""
        
    col_kabel, col_sn = st.columns(2)
    with col_kabel:
        st.markdown("### 🧵 1. Input Pengeluaran Kabel Precon")
        with st.container(border=True):
            tek_kabel = st.selectbox("Pilih Tim / Teknisi (Kabel):", DAFTAR_TEKNISI, key="tek_kabel")
            pilihan_kabel = st.selectbox("Pilih Jenis / Ukuran Kabel Precon:", DAFTAR_KABEL_OTOMATIS, key="pilihan_kabel")
            wo_kabel = st.text_input("Nomor WO / Keterangan (Kabel):", key="wo_kabel")
            if st.button("➕ Simpan Kabel ke Log", use_container_width=True, type="primary"):
                new_row = {
                    'Waktu Scan': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Nama Teknisi': tek_kabel, 'Serial Number (SN)': "-", 'Nama Barang': "Kabel Precon",
                    'Kabel Precon': pilihan_kabel, 'No WO / Keterangan': wo_kabel if wo_kabel else "-"
                }
                st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
                st.toast("Berhasil menyimpan data kabel!", icon="🧵")

    with col_sn:
        st.markdown("### 📟 2. Scan Otomatis SN Device (ONT / STB)")
        with st.container(border=True):
            st.selectbox("Pilih Tim / Teknisi (Device):", DAFTAR_TEKNISI, key="tek_device")
            st.text_input("Nomor WO / Keterangan (Device):", key="wo_device")
            st.text_input("KOTAK SCANNER SN:", placeholder="Tembak barcode SN ke sini...", key="scan_sn_key", on_change=proses_scan_sn)

    st.markdown("---")
    if not st.session_state.log_scan_harian.empty:
        st.dataframe(st.session_state.log_scan_harian, use_container_width=True)
    else:
        st.info("Belum ada data material yang di-input atau di-scan hari ini.")

# ==================== MENU 2: MASTER SN ====================
elif menu == "🔍 Lihat & Cari Master SN":
    st.subheader("🔍 Pusat Data Master SN")
    st.dataframe(df_master, use_container_width=True)

# ==================== MENU 3: STOK GUDANG ====================
elif menu == "📦 Stok Gudang":
    st.subheader("📦 Data Stok Gudang")
    t1, t2 = st.tabs(["📟 Device", "🧵 Kabel PRECON"])
    with t1:
        if df_device is not None: st.dataframe(df_device, use_container_width=True)
        else: st.info(f"File Excel '{EXCEL_FILE}' tidak terdeteksi atau sheet 'Stock Device' salah nama.")
    with t2:
        if df_precon is not None: st.dataframe(df_precon, use_container_width=True)
        else: st.info(f"File Excel '{EXCEL_FILE}' tidak terdeteksi atau sheet 'Stock PRECON' salah nama.")

# ==================== MENU 4: HISTORI EXCEL TEKNISI ====================
elif menu == "👨‍🔧 Histori Excel Teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan = st.selectbox("Pilih Nama Tim:", DAFTAR_TEKNISI)
    df_tek = load_excel_sheet(pilihan)
    if df_tek is not None: st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
    else: st.info(f"Sheet bernama '{pilihan}' tidak ditemukan di dalam file Excel '{EXCEL_FILE}'.")
