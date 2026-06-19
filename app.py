import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi halaman utama (Wajib paling atas)
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

st.title("⚡ Sistem Logistik IKR Metech")

# --- DETEKSI FILE DI GITHUB (OTOMATIS) ---
semua_file = os.listdir('.')

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

# --- DEKLARASI SESSION STATE UTAMA ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = pd.DataFrame(
        columns=[
            'Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 
            'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore'
        ]
    )

if 'pesan_sukses' not in st.session_state:
    st.session_state.pesan_sukses = ""
    
if 'pesan_error' not in st.session_state:
    st.session_state.pesan_error = ""

if 'status_scan_terakhir' not in st.session_state:
    st.session_state.status_scan_terakhir = "kosong"

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

# --- AUTOMATIC CALLBACK SCAN SN (PAGI) ---
def proses_scan_sn():
    sn_value = st.session_state.scan_sn_key.strip()
    if sn_value:
        # 1. Proteksi Anti-Double Scan
        if not st.session_state.log_scan_harian.empty:
            sn_terdata = st.session_state.log_scan_harian['Serial Number (SN)'].astype(str).str.lower().values
            if sn_value.lower() in sn_terdata:
                st.session_state.pesan_error = f"🚨 SCAN DITOLAK! SN '{sn_value}' sudah di-scan hari ini!"
                st.session_state.pesan_sukses = ""
                st.session_state.status_scan_terakhir = "double"
                st.session_state.scan_sn_key = ""
                return
        
        # 2. Validasi ke master SN
        pencarian = df_master[df_master['SN'].astype(str).str.lower() == sn_value.lower()]
        nama_barang = pencarian.iloc[0].get('Nama_Barang', 'Device Terdaftar') if not pencarian.empty else "ONT/STB (Manual/Tidak di Master)"
        
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = {
            'Waktu Scan': waktu_sekarang,
            'Nama Teknisi': st.session_state.tek_device, 
            'Serial Number (SN)': sn_value,
            'Nama Barang': nama_barang, 
            'Kabel Precon': "-", 
            'No WO / Keterangan': st.session_state.wo_device if st.session_state.wo_device else "-",
            'Status Pemasangan Sore': "Belum Dilaporkan ⏳",
            'Keterangan Tambahan Sore': "-"
        }
        st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' ({nama_barang}) tersimpan!"
        st.session_state.pesan_error = ""
        st.session_state.status_scan_terakhir = "sukses"
        st.session_state.scan_sn_key = ""

# --- SIDEBAR NAVIGASI ---
st.sidebar.markdown("### 📊 NAVIGATION MENU")
menu = st.sidebar.radio(
    "PILIH HALAMAN APLIKASI:", 
    [
        "✍️ Scan & Input Pagi (Pengeluaran)", 
        "📝 Laporan Penggunaan Sore (Update Status)", 
        "📦 Lihat Stok Gudang", 
        "👨‍🔧 Histori Sheet Teknisi"
    ]
)

# ==================== MENU 1: SCAN & INPUT PAGI ====================
if menu == "✍️ Scan & Input Pagi (Pengeluaran)":
    st.subheader("✍️ Pendataan Pengeluaran Material Harian (Pagi/Siang)")
    
    if st.session_state.pesan_sukses:
        st.success(st.session_state.pesan_sukses)
        st.session_state.pesan_sukses = ""
    if st.session_state.pesan_error:
        st.error(st.session_state.pesan_error)
        st.session_state.pesan_error = ""
        
    col_kabel, col_sn = st.columns(2)
    with col_kabel:
        st.markdown("#### 🧵 1. Input Pengeluaran Kabel Precon")
        with st.container(border=True):
            tek_kabel = st.selectbox("Pilih Tim / Teknisi (Kabel):", DAFTAR_TEKNISI, key="tek_kabel")
            pilihan_kabel = st.selectbox("Pilih Jenis / Ukuran Kabel Precon:", DAFTAR_KABEL_OTOMATIS, key="pilihan_kabel")
            wo_kabel = st.text_input("Nomor WO / Keterangan (Kabel):", key="wo_kabel")
            if st.button("➕ Simpan Kabel ke Log", use_container_width=True, type="primary"):
                new_row = {
                    'Waktu Scan': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Nama Teknisi': tek_kabel, 'Serial Number (SN)': "-", 'Nama Barang': "Kabel Precon",
                    'Kabel Precon': pilihan_kabel, 'No WO / Keterangan': wo_kabel if wo_kabel else "-",
                    'Status Pemasangan Sore': "Belum Dilaporkan ⏳",
                    'Keterangan Tambahan Sore': "-"
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
                st.text_input(
                    "KOTAK SCANNER SN", 
                    placeholder="Tembak barcode SN ke sini...", 
                    key="scan_sn_key", 
                    on_change=proses_scan_sn,
                    label_visibility="collapsed"
                )
                
            with col_icon_status:
                if st.session_state.status_scan_terakhir == "sukses":
                    st.markdown("<p style='font-size: 26px; margin: 0; padding-top: 2px; text-align: center;'>✅</p>", unsafe_allow_html=True)
                elif st.session_state.status_scan_terakhir == "double":
                    st.markdown("<p style='font-size: 26px; margin: 0; padding-top: 2px; text-align: center;'>❌</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-size: 26px; margin: 0; padding-top: 2px; text-align: center; color: gray;'>➖</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 Tabel Pengeluaran Barang Hari Ini")
    if not st.session_state.log_scan_harian.empty:
        st.dataframe(st.session_state.log_scan_harian, use_container_width=True)
        
        if st.button("🗑️ Kosongkan Tabel Pagi (Reset)"):
            st.session_state.log_scan_harian = pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore'])
            st.session_state.status_scan_terakhir = "kosong"
            st.rerun()
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU LAPORAN SORE VERSI INTERAKTIF ====================
elif menu == "📝 Laporan Penggunaan Sore (Update Status)":
    st.subheader("📝 Laporan Hasil Kerja Lapangan Sore Hari")
    st.info("💡 CARA PENGGUNAAN: Cukup lihat grup Telegram kamu. Lalu pada tabel di bawah, KLIK ganda pada kolom 'Status Pemasangan Sore' untuk merubah status, atau KLIK ganda pada 'Keterangan Tambahan Sore' untuk mengetik catatan lapangan. Tidak perlu scan ulang!")
    
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
                "Status Pemasangan Sore": st.column_config.SelectColumn(
                    "Status Pemasangan Sore",
                    options=["Belum Dilaporkan ⏳", "Sudah Terinstal ✅", "Belum Terinstal / Retur ❌"],
                    required=True
                ),
                "Keterangan Tambahan Sore": st.column_config.TextColumn("Keterangan Tambahan Sore (Ketik Sini)")
            },
            disabled=["Waktu Scan", "Nama Teknisi", "Serial Number (SN)", "Nama Barang", "Kabel Precon", "No WO / Keterangan"],
            use_container_width=True,
            key="gudang_editor_sore"
        )
        
        st.session_state.log_scan_harian = tabel_edit_sore
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📥 Download Hasil Rekapitulasi Berkas Lengkap")
        
        csv_final_data = st.session_state.log_scan_harian.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Berkas Logistik Harian (.CSV)", 
            data=csv_final_data, 
            file_name=f"REKAP_IKR_METECH_{datetime.now().strftime('%Y%m%d')}.csv", 
            mime="text/csv", 
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning("Data kosong. Silakan input atau scan material di menu Pagi terlebih dahulu.")

# ==================== MENU 3: STOK GUDANG ====================
elif menu == "📦 Lihat Stok Gudang":
    st.subheader("📦 Data Stok Gudang Asli")
    t1, t2 = st.tabs(["📟 Device", "🧵 Kabel PRECON"])
    with t1:
        if df_device is not None: st.dataframe(df_device, use_container_width=True)
        else: st.info(f"File Excel '{EXCEL_FILE}' tidak terdeteksi atau sheet 'Stock Device' kosong.")
    with t2:
        if df_precon is not None: st.dataframe(df_precon, use_container_width=True)
        else: st.info(f"File Excel '{EXCEL_FILE}' tidak terdeteksi atau sheet 'Stock PRECON' kosong.")

# ==================== MENU 4: HISTORI EXCEL TEKNISI ====================
elif menu == "👨‍🔧 Histori Sheet Teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan = st.selectbox("Pilih Nama Tim:", DAFTAR_TEKNISI)
    df_tek = load_excel_sheet(pilihan)
    if df_tek is not None: st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
    else: st.info(f"Sheet bernama '{pilihan}' tidak ditemukan di dalam file Excel '{EXCEL_FILE}'.")
