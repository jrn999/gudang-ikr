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

# NAMA FILE DI GITHUB
EXCEL_FILE = "MATERIAL IKR [ KEBUTUHAN WO HARIAN ].xlsx"
MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"

# --- DEKLARASI SESSION STATE ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = pd.DataFrame(
        columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan']
    )
if 'pesan_sukses' not in st.session_state:
    st.session_state.pesan_sukses = ""

# Fungsi loading data master SN
@st.cache_data
def load_master_sn():
    if os.path.exists(MASTER_SN_FILE):
        try:
            df = pd.read_csv(MASTER_SN_FILE)
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])
    return pd.DataFrame(columns=['SN', 'Nama_Barang', 'Kode_Gudang', 'Deskripsi'])

# Fungsi loading sheet Excel
@st.cache_data
def load_excel_sheet(sheet_name):
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, engine='openpyxl')
            # Bersihkan spasi gaib di nama kolom jika ada
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            return None
    return None

# --- LOAD DATA ---
df_master = load_master_sn()
df_device = load_excel_sheet("Stock Device")
df_precon = load_excel_sheet("Stock PRECON")

# --- PROSES MEMBUAT DAFTAR KABEL OTOMATIS DARI EXCEL ---
DAFTAR_KABEL_OTOMATIS = []
if df_precon is not None and 'Description' in df_precon.columns:
    # Mengambil kolom Description, membuang baris kosong, dan mengubah ke list
    list_kabel = df_precon['Description'].dropna().astype(str).tolist()
    # Filter hanya baris yang mengandung informasi kabel (menghindari baris Total/Keterangan lain)
    DAFTAR_KABEL_OTOMATIS = [kabel.strip() for kabel in list_kabel if "CABLE" in kabel or "MTR" in kabel]

# Jika karena suatu hal file excel tidak terbaca, gunakan fallback list lengkap ini
if not DAFTAR_KABEL_OTOMATIS:
    DAFTAR_KABEL_OTOMATIS = [
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 125MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 175MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 225MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 300MTR",
        "FIBERART - CABLE PRECON SC/UPC-SC/APC - 75MTR",
        "FIBERART - CABLE PRECON SC/UPC-SC/APC - 300MTR",
        "NEXTFIBER - CABLE PRECON SC/UPC-SC/APC - 300MTR"
    ]

# Daftar 10 Tim Teknisi
DAFTAR_TEKNISI = [
    "PUTRA-SONY", "RIYAN-RIYADI", "NADI-PARI", "ARIF-YASRIL", 
    "NOVANS-GOBY", "PERI-ROBIN", "TEDI-DODI", "REFKY-DODI", 
    "RAHMAN-AGUS", "IDDO-NAUFAL"
]

# --- SAKTI AUTOMATIC CALLBACK: LANGSUNG BERHASIL BEGITU SELESAI SCAN ---
def proses_scan_sn():
    sn_value = st.session_state.scan_sn_key.strip()
    if sn_value:
        # Validasi otomatis ke data master SN
        pencarian = df_master[df_master['SN'].astype(str).str.lower() == sn_value.lower()]
        if not pencarian.empty:
            nama_barang = pencarian.iloc[0].get('Nama_Barang', 'Device Terdaftar')
        else:
            nama_barang = "ONT/STB (Manual/Tidak di Master)"
        
        # Masukkan langsung ke database log harian
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = {
            'Waktu Scan': waktu_sekarang,
            'Nama Teknisi': st.session_state.tek_device,
            'Serial Number (SN)': sn_value,
            'Nama Barang': nama_barang,
            'Kabel Precon': "-",
            'No WO / Keterangan': st.session_state.wo_device if st.session_state.wo_device else "-"
        }
        st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' ({nama_barang}) untuk tim {st.session_state.tek_device} langsung tersimpan!"
        
        # SAKTI: Mengosongkan kolom input secara otomatis agar siap untuk scan SN berikutnya
        st.session_state.scan_sn_key = ""

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("🛠️ Logistik IKR Cloud")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "PILIH MENU APLIKASI:",
    [
        "📊 Dashboard Utama", 
        "✍️ Input & Scan Harian Teknisi", 
        "🔍 Lihat & Cari Master SN", 
        "📦 Stok Gudang", 
        "👨‍🔧 Monitoring Sheet Teknisi"
    ]
)

# ==================== 1. DASHBOARD UTAMA ====================
if menu == "📊 Dashboard Utama":
    st.title("📊 Dashboard Utama Gudang")
    total_sn = len(df_master)
    total_input_hari_ini = len(st.session_state.log_scan_harian)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Master SN Terdaftar", value=f"{int(total_sn)} Item")
    with col2:
        st.metric(label="Material Terdata Hari Ini", value=f"{int(total_input_hari_ini)} Item", delta="Live")
        
    st.markdown("### 📌 Status File Gudang di GitHub")
    if os.path.exists(MASTER_SN_FILE):
        st.success(f"✅ Master SN Terkoneksi Sempurna ({MASTER_SN_FILE})")
    else:
        st.error(f"❌ File '{MASTER_SN_FILE}' tidak ditemukan di GitHub!")

# ==================== 2. INPUT & SCAN HARIAN TEKNISI ====================
elif menu == "✍️ Input & Scan Harian Teknisi":
    st.title("✍️ Pendataan Material Harian Teknisi")
    st.write("Menu inputan terpisah mandiri demi akurasi dan sinkronisasi data.")
    
    # Notifikasi Pop-up Hijau saat Berhasil Scan SN
    if st.session_state.pesan_sukses:
        st.success(st.session_state.pesan_sukses)
        st.session_state.pesan_sukses = "" # Clear message after displaying
        
    col_kabel, col_sn = st.columns(2)
    
    # ---------------- KOLOM KIRI: KHUSUS INPUT KABEL PRECON (OTOMATIS SESUAI EXCEL) ----------------
    with col_kabel:
        st.markdown("### 🧵 1. Input Pengeluaran Kabel Precon")
        with st.container(border=True):
            tek_kabel = st.selectbox("Pilih Tim / Teknisi (Kabel):", DAFTAR_TEKNISI, key="tek_kabel")
            
            # DROPDOWN INI SEKARANG OTOMATIS SAMA DENGAN ISI FILE EXCEL STOCK PRECON KAMU
            pilihan_kabel = st.selectbox("Pilih Jenis / Ukuran Kabel Precon:", DAFTAR_KABEL_OTOMATIS, key="pilihan_kabel")
            
            wo_kabel = st.text_input("Nomor WO / Keterangan (Kabel):", placeholder="Contoh: WO-KABEL-01", key="wo_kabel")
            
            st.markdown("<br>", unsafe_allow_html=True)
            tombol_kabel = st.button("➕ Simpan Kabel ke Log", use_container_width=True, type="primary")
            if tombol_kabel:
                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = {
                    'Waktu Scan': waktu_sekarang,
                    'Nama Teknisi': tek_kabel,
                    'Serial Number (SN)': "-",
                    'Nama Barang': "Kabel Precon",
                    'Kabel Precon': pilihan_kabel,
                    'No WO / Keterangan': wo_kabel if wo_kabel else "-"
                }
                st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
                st.toast(f"Berhasil menyimpan data kabel untuk {tek_kabel}!", icon="🧵")

    # ---------------- KOLOM KANAN: KHUSUS AUTO-SCAN DEVICE (ONT/STB) ----------------
    with col_sn:
        st.markdown("### 📟 2. Scan Otomatis SN Device (ONT / STB)")
        with st.container(border=True):
            st.selectbox("Pilih Tim / Teknisi (Device):", DAFTAR_TEKNISI, key="tek_device")
            st.text_input("Nomor WO / Keterangan (Device):", placeholder="Contoh: WO-ONT-99", key="wo_device")
            
            st.markdown("👇 **ARAHKAN KURSOR DAN SCAN BARCODE SN DI BAWAH INI:**")
            st.text_input(
                "KOTAK SCANNER SN:", 
                placeholder="Tembak barcode SN ke sini...", 
                key="scan_sn_key", 
                on_change=proses_scan_sn
            )
            st.info("💡 **Langsung Berhasil:** Begitu barcode di-scan (atau ditekan enter), data amblas masuk ke tabel bawah, notifikasi sukses muncul, dan kotak input langsung otomatis bersih kosong kembali!")

    # Tampilkan Tabel Live Hasil Pendataan Hari Ini
    st.markdown("---")
    st.subheader("📋 Tabel Gabungan Hasil Log Pengeluaran Hari Ini")
    
    if not st.session_state.log_scan_harian.empty:
        st.dataframe(st.session_state.log_scan_harian, use_container_width=True)
        
        # Tombol Download Excel Instan
        csv_data = st.session_state.log_scan_harian.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Scan Hari Ini (.CSV / Excel)",
            data=csv_data,
            file_name=f"LOG_IKR_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Tombol Reset Tabel
        if st.button("🗑️ Kosongkan Tabel Hari Ini (Reset)"):
            st.session_state.log_scan_harian = pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan'])
            st.rerun()
    else:
        st.info("Belum ada data material yang di-input atau di-scan hari ini.")

# ==================== 3. LIHAT & CARI MASTER SN ====================
elif menu == "🔍 Lihat & Cari Master SN":
    st.title("🔍 Pusat Data Master SN")
    st.dataframe(df_master, use_container_width=True)

# ==================== 4. STOK GUDANG ====================
elif menu == "📦 Stok Gudang":
    st.title("📦 Data Stok Gudang")
    t1, t2 = st.tabs(["📟 Device", "🧵 Kabel PRECON"])
    with t1:
        if df_device is not None: st.dataframe(df_device, use_container_width=True)
        else: st.info("File Excel harian tidak terdeteksi di GitHub.")
    with t2:
        if df_precon is not None: st.dataframe(df_precon, use_container_width=True)
        else: st.info("File Excel harian tidak terdeteksi di GitHub.")

# ==================== 5. MONITORING SHEET TEKNISI ====================
elif menu == "👨‍🔧 Monitoring Sheet Teknisi":
    st.title("👨‍🔧 Histori Penggunaan Excel Asli Teknisi")
    pilihan = st.selectbox("Pilih Nama Tim:", DAFTAR_TEKNISI)
    df_tek = load_excel_sheet(pilihan)
    if df_tek is not None: 
        st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
    else: 
        st.info("Data harian dari Excel utama belum di-upload ke GitHub.")
