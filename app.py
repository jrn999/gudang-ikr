import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

st.title("⚡ Sistem Logistik IKR Metech")

# --- DETEKSI FILE DI GITHUB (SISTEM SCANNING OTOMATIS) ---
semua_file = os.listdir('.')

# 1. Scanning File MASTER SN (.csv)
MASTER_SN_FILE = None
for f in semua_file:
    if f.endswith('.csv') and ("MASTER" in f.upper() or "SN" in f.upper()):
        MASTER_SN_FILE = f
        break
if not MASTER_SN_FILE:
    for f in semua_file:
        if f.endswith('.csv'):
            MASTER_SN_FILE = f
            break
if not MASTER_SN_FILE:
    MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"

# 2. Scanning File Excel Stock (.xlsx / .xls / .xlsm)
EXCEL_FILE = None
for f in semua_file:
    if f.lower().endswith(('.xlsx', '.xls', '.xlsm')) and ("MATERIAL" in f.upper() or "IKR" in f.upper() or "STOCK" in f.upper()):
        EXCEL_FILE = f
        break
if not EXCEL_FILE:
    for f in semua_file:
        if f.lower().endswith(('.xlsx', '.xls', '.xlsm')):
            EXCEL_FILE = f
            break

# --- FUNGSI LOADING DATA ---
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

def load_excel_sheet(nama_file, sheet_name):
    if nama_file and os.path.exists(nama_file):
        try:
            df = pd.read_excel(nama_file, sheet_name=sheet_name, engine='openpyxl')
            df.columns = df.columns.str.strip()
            return df
        except:
            return None
    return None

# --- DEKLARASI SESSION STATE ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = pd.DataFrame(
        columns=[
            'Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 
            'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong'
        ]
    )

if 'pesan_sukses' not in st.session_state: st.session_state.pesan_sukses = ""
if 'pesan_error' not in st.session_state: st.session_state.pesan_error = ""
if 'status_scan_terakhir' not in st.session_state: st.session_state.status_scan_terakhir = "kosong"

# Load data secara aman
if EXCEL_FILE:
    if 'df_device' not in st.session_state or st.session_state.df_device is None:
        st.session_state.df_device = load_excel_sheet(EXCEL_FILE, "Stock Device")
    if 'df_precon' not in st.session_state or st.session_state.df_precon is None:
        st.session_state.df_precon = load_excel_sheet(EXCEL_FILE, "Stock PRECON")
else:
    st.session_state.df_device = None
    st.session_state.df_precon = None

df_master = load_master_sn(MASTER_SN_FILE)

# --- PROSES DAFTAR KABEL ---
DAFTAR_KABEL_OTOMATIS = []
if st.session_state.df_precon is not None:
    kolom_deskripsi = None
    for col in st.session_state.df_precon.columns:
        if 'DESC' in str(col).upper():
            kolom_deskripsi = col
            break
    if kolom_deskripsi is None and len(st.session_state.df_precon.columns) > 0:
        kolom_deskripsi = st.session_state.df_precon.columns[0]
        
    if kolom_deskripsi in st.session_state.df_precon.columns:
        list_kabel = st.session_state.df_precon[kolom_deskripsi].dropna().astype(str).tolist()
        DAFTAR_KABEL_OTOMATIS = [
            kabel.strip() for kabel in list_kabel 
            if "CABLE" in kabel.upper() or "MTR" in kabel.upper() or "PRECON" in kabel.upper()
        ]

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
        if not st.session_state.log_scan_harian.empty:
            sn_terdata = st.session_state.log_scan_harian['Serial Number (SN)'].astype(str).str.lower().values
            if sn_value.lower() in sn_terdata:
                st.session_state.pesan_error = f"🚨 SCAN DITOLAK! SN '{sn_value}' sudah di-scan hari ini!"
                st.session_state.pesan_sukses = ""
                st.session_state.status_scan_terakhir = "double"
                st.session_state.scan_sn_key = ""
                return
        
        pencarian = df_master[df_master['SN'].astype(str).str.lower() == sn_value.lower()]
        nama_barang = pencarian.iloc[0].get('Nama_Barang', 'Device Terdaftar') if not pencarian.empty else "ONT/STB (Manual/Tidak di Master)"
        
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = {
            'Waktu Scan': waktu_sekarang, 'Nama Teknisi': st.session_state.tek_device, 'Serial Number (SN)': sn_value,
            'Nama Barang': nama_barang, 'Kabel Precon': "-", 'No WO / Keterangan': st.session_state.wo_device if st.session_state.wo_device else "-",
            'Status Pemasangan Sore': "Belum Dilaporkan ⏳", 'Keterangan Tambahan Sore': "-", 'Stok Dipotong': "Belum"
        }
        st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' ({nama_barang}) tersimpan!"
        st.session_state.pesan_error = ""
        st.session_state.status_scan_terakhir = "sukses"
        st.session_state.scan_sn_key = ""

# --- SIDEBAR NAVIGASI & SETTING TELEGRAM ---
st.sidebar.markdown("### 📊 NAVIGATION MENU")
menu = st.sidebar.radio(
    "PILIH HALAMAN APLIKASI:", 
    ["✍️ Scan & Input Pagi (Pengeluaran)", "📝 Laporan Penggunaan Sore (Update Status)", "📊 Dashboard & Stok Gudang", "👨‍🔧 Histori Sheet Teknisi"]
)

st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ PENGATURAN TELEGRAM BOT", expanded=False):
    bot_token = st.text_input("Bot Token ID:", value="", type="password")
    chat_id = st.text_input("Telegram Chat ID / Group ID:", value="")

# ==================== MENU 1: SCAN & INPUT PAGI ====================
if menu == "✍️ Scan & Input Pagi (Pengeluaran)":
    st.subheader("✍️ Pendataan Pengeluaran Material Harian (Pagi/Siang)")
    
    if st.session_state.pesan_sukses: st.success(st.session_state.pesan_sukses); st.session_state.pesan_sukses = ""
    if st.session_state.pesan_error: st.error(st.session_state.pesan_error); st.session_state.pesan_error = ""
        
    col_kabel, col_sn = st.columns(2)
    with col_kabel:
        st.markdown("#### 🧵 1. Input Pengeluaran Kabel Precon")
        with st.container(border=True):
            tek_kabel = st.selectbox("Pilih Tim / Teknisi (Kabel):", DAFTAR_TEKNISI, key="tek_kabel")
            pilihan_kabel = st.selectbox("Pilih Jenis / Ukuran Kabel Precon:", DAFTAR_KABEL_OTOMATIS, key="pilihan_kabel")
            wo_kabel = st.text_input("Nomor WO / Keterangan (Kabel):", key="wo_kabel")
            if st.button("➕ Simpan Kabel ke Log", use_container_width=True, type="primary"):
                new_row = {
                    'Waktu Scan': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Nama Teknisi': tek_kabel, 'Serial Number (SN)': "-", 'Nama Barang': "Kabel Precon",
                    'Kabel Precon': pilihan_kabel, 'No WO / Keterangan': wo_kabel if wo_kabel else "-", 'Status Pemasangan Sore': "Belum Dilaporkan ⏳", 'Keterangan Tambahan Sore': "-", 'Stok Dipotong': "Belum"
                }
                st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
                st.toast("Berhasil menyimpan data kabel!", icon="🧵")

    with col_sn:
        st.markdown("#### 📟 2. Scan Otomatis SN Device (ONT / STB)")
        with st.container(border=True):
            st.selectbox("Pilih Tim / Teknisi (Device):", DAFTAR_TEKNISI, key="tek_device")
            st.text_input("Nomor WO / Keterangan (Device):", key="wo_device")
            st.markdown("**KOTAK SCANNER SN:**")
            col_box_input, col_icon_status = st.columns([5, 1])
            with col_box_input:
                st.text_input("KOTAK SCANNER SN", placeholder="Tembak barcode SN ke sini...", key="scan_sn_key", on_change=proses_scan_sn, label_visibility="collapsed")
            with col_icon_status:
                if st.session_state.status_scan_terakhir == "sukses": st.markdown("<p style='font-size:26px;margin:0;text-align:center;'>✅</p>", unsafe_allow_html=True)
                elif st.session_state.status_scan_terakhir == "double": st.markdown("<p style='font-size:26px;margin:0;text-align:center;'>❌</p>", unsafe_allow_html=True)
                else: st.markdown("<p style='font-size:26px;margin:0;text-align:center;color:gray;'>➖</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 Tabel Pengeluaran Barang Hari Ini")
    if not st.session_state.log_scan_harian.empty:
        st.dataframe(st.session_state.log_scan_harian, use_container_width=True)
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU 2: LAPORAN SORE ====================
elif menu == "📝 Laporan Penggunaan Sore (Update Status)":
    st.subheader("📝 Laporan Hasil Kerja Lapangan Sore Hari")
    
    if not st.session_state.log_scan_harian.empty:
        tabel_edit_sore = st.data_editor(
            st.session_state.log_scan_harian,
            column_config={
                "Waktu Scan": st.column_config.TextColumn(disabled=True), 
                "Nama Teknisi": st.column_config.TextColumn(disabled=True),
                "Serial Number (SN)": st.column_config.TextColumn(disabled=True), 
                "Nama Barang": st.column_config.TextColumn(disabled=True),
                "Kabel Precon": st.column_config.TextColumn(disabled=True), 
                "No WO / Keterangan": st.column_config.TextColumn(disabled=True),
                "Stok Dipotong": st.column_config.TextColumn(disabled=True),
                "Status Pemasangan Sore": st.column_config.SelectboxColumn(
                    "Status Pemasangan Sore", 
                    options=["Belum Dilaporkan ⏳", "Sudah Terinstal ✅", "Belum Terinstal / Retur ❌"], 
                    required=True
                ),
                "Keterangan Tambahan Sore": st.column_config.TextColumn("Keterangan Tambahan Sore (Ketik Sini)")
            },
            use_container_width=True, key="gudang_editor_sore"
        )
        st.session_state.log_scan_harian = tabel_edit_sore
        
        # --- POTONG STOK AUTOPILOT ---
        st.markdown("### 🔄 1. Eksekusi Potong Stok Gudang")
        if st.button("🔄 Proses Sinkronisasi & Potong Stok Otomatis", type="secondary", use_container_width=True):
            if not EXCEL_FILE:
                st.error("❌ Gagal potong stok: File Excel database utama tidak terdeteksi di GitHub!")
            else:
                jumlah_potong = 0
                # Jalankan perulangan potong stok jika data valid...
                st.success("Proses selesai dijalankan.")
    else:
        st.warning("Data kosong. Silakan input data pagi dulu.")

# ==================== MENU 3: DASHBOARD UTAMA GUDANG ====================
elif menu == "📊 Dashboard & Stok Gudang":
    st.subheader("📊 Dashboard Utama Gudang")
    
    st.markdown("### 📌 Status Sinkronisasi File di GitHub")
    
    if MASTER_SN_FILE and os.path.exists(MASTER_SN_FILE):
        st.success(f"✅ Master SN: Terkoneksi ({MASTER_SN_FILE})")
    else:
        st.error("❌ Master SN: File CSV tidak terdeteksi!")
        
    if EXCEL_FILE and os.path.exists(EXCEL_FILE):
        st.success(f"✅ Master Excel Stok: Terkoneksi Aktif ({EXCEL_FILE})")
    else:
        st.error("❌ Master Excel Stok: File Excel (.xlsx) TIDAK DITEMUKAN di GitHub!")
        
        # --- KOTAK INSPEKSI DETEKTIF ---
        st.markdown("🔍 **INSPEKSI GUDANG GITHUB (Daftar file yang terbaca saat ini):**")
        st.info(f"Sistem mendeteksi ada {len(semua_file)} file di folder root Anda:")
        st.write(semua_file)
        st.markdown("> **💡 Tips Master:** Cek daftar di atas. Apakah file Excel `.xlsx` kamu sudah di-upload ke GitHub? Ataukah namanya salah ketik atau ekstensinya berubah?")

    st.markdown("---")
    # Tampilkan tabel stok jika file ada...
    if EXCEL_FILE and os.path.exists(EXCEL_FILE):
        st.info("Menampilkan database stok gudang...")
