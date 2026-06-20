import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
from github import Github
import io

# 1. Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

# 2. INJEKSI ADVANCED CSS (Merubah Streamlit Menjadi Seperti Tampilan image_b242de.jpg)
st.markdown("""
<style>
    /* Sembunyikan hiasan bawaan Streamlit */
    [data-testid="stDecoration"], [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Ubah warna background utama aplikasi */
    .stApp {
        background-color: #f4f6f9 !important;
    }
    
    /* STYLING SIDEBAR (Gradasi Ungu & Text Putih) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4b5cc4 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Hilangkan lingkaran/dot asli pada Radio Button Sidebar */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* Rombak list radio menjadi menu flat yang elegan */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 6px !important;
    }
    
    [data-testid="stSidebar"] div[data-testid="stRadio"] label {
        padding: 12px 20px !important;
        color: #e2e8f0 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border-radius: 0px 8px 8px 0px !important;
        margin-right: 15px !important;
        border-left: 4px solid transparent !important;
        background-color: transparent !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    /* Efek Hover Menu Sidebar */
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    
    /* MENU AKTIF (Garis Kuning + Background Agak Terang sesuai image_b242de.jpg) */
    [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-left: 4px solid #facc15 !important;
        font-weight: 600 !important;
    }
    
    /* STYLING KOTAK / CONTAINER UTAMA (Bentuk Card Putih + Shadow Halus) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white !important;
        border-radius: 12px !important;
        box-shadow: 0px 4px 16px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid #eef2f6 !important;
        padding: 28px !important;
        margin-bottom: 20px !important;
    }
    
    /* Modifikasi Form Input & Text Area */
    div[data-testid="stWidgetLabel"] p {
        font-weight: 500 !important;
        color: #4b5563 !important;
        font-size: 14px !important;
        margin-bottom: 4px !important;
    }
    
    input, select, textarea {
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* Tombol Utama (Warna Ungu) */
    button[kind="primary"] {
        background-color: #764ba2 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        box-shadow: 0px 2px 6px rgba(118, 75, 162, 0.3) !important;
    }
    button[kind="primary"]:hover {
        background-color: #5c348a !important;
    }
</style>
""", unsafe_allow_html=True)

# --- AMBIL KREDENSIAL GITHUB DARI SECRETS ---
GITHUB_TOKEN = ""
REPO_NAME = ""

try:
    if "GITHUB_TOKEN" in st.secrets:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    if "GITHUB_REPO" in st.secrets:
        REPO_NAME = st.secrets["GITHUB_REPO"]
except Exception:
    pass

# --- 1. SCAN & SELEKSI FILE MASTER SN LOKAL ---
semua_file = os.listdir('.')
MASTER_SN_FILE = None
for f in semua_file:
    if f.endswith('.csv') and ("MASTER" in f.upper() or "SN" in f.upper()):
        MASTER_SN_FILE = f
        break
if not MASTER_SN_FILE: 
    MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"

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

df_master = load_master_sn(MASTER_SN_FILE)

# --- 2. PREPARE DATASET DEFAULT ---
if not df_master.empty and 'Nama_Barang' in df_master.columns:
    df_counts = df_master['Nama_Barang'].value_counts().reset_index()
    df_counts.columns = ['Nama Barang', 'Stok Gudang']
    baris_cadangan = pd.DataFrame([
        {'Nama Barang': 'ONT/STB (Manual/Tidak di Master)', 'Stok Gudang': 0},
        {'Nama Barang': 'Device Terdaftar', 'Stok Gudang': 0}
    ])
    df_device_default = pd.concat([df_counts, baris_cadangan], ignore_index=True)
else:
    df_device_default = pd.DataFrame({
        'Nama Barang': ['ONT Premium', 'STB HD Box', 'Access Point Outdoor', 'ONT/STB (Manual/Tidak di Master)', 'Device Terdaftar'],
        'Stok Gudang': [0, 0, 0, 0, 0]
    })

df_precon_default = pd.DataFrame({
    'Nama Material': [
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 125MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 175MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 225MTR",
        "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 300MTR"
    ],
    'Stok Gudang': [50, 50, 50, 50, 50]
})

df_teknisi_default = pd.DataFrame({
    'Nama Teknisi': ["PUTRA-SONY", "RIYAN-RIYADI", "NADI-PARI", "ARIF-YASRIL", "NOVANS-GOBY", "PERI-ROBIN", "TEDI-DODI", "REFKY-DODI", "RAHMAN-AGUS", "IDDO-NAUFAL"]
})

def load_atau_buat_file_github(nama_file, df_default):
    if not GITHUB_TOKEN or not REPO_NAME:
        return df_default
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        try:
            repo.get_branch("data-log")
        except Exception:
            main_branch = repo.get_branch("main")
            repo.create_git_ref(ref="refs/heads/data-log", sha=main_branch.commit.sha)
            
        try:
            contents = repo.get_contents(nama_file, ref="data-log")
            df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')))
            df.columns = df.columns.str.strip()
            return df
        except Exception:
            csv_string = df_default.to_csv(index=False)
            repo.create_file(nama_file, f"Inisialisasi Otomatis {nama_file}", csv_string, branch="data-log")
            return df_default
    except Exception as e:
        return df_default

def simpan_file_ke_github(nama_file, df, pesan_commit="Auto-Update"):
    if not GITHUB_TOKEN or not REPO_NAME:
        return
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        csv_string = df.to_csv(index=False)
        try:
            contents = repo.get_contents(nama_file, ref="data-log")
            repo.update_file(
                nama_file, 
                f"{pesan_commit} {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                csv_string, 
                contents.sha, 
                branch="data-log"
            )
        except Exception:
            repo.create_file(nama_file, f"Inisialisasi {nama_file}", csv_string, branch="data-log")
    except Exception as e:
        st.error(f"🚨 Gagal sinkronisasi {nama_file} ke GitHub: {e}")

# --- SINKRONISASI DATABASES ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = load_atau_buat_file_github("log_harian.csv", pd.DataFrame(
        columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong']
    ))

if 'df_device' not in st.session_state or st.session_state.df_device is None:
    st.session_state.df_device = load_atau_buat_file_github("database_device.csv", df_device_default)

if 'df_precon' not in st.session_state or st.session_state.df_precon is None:
    st.session_state.df_precon = load_atau_buat_file_github("database_precon.csv", df_precon_default)

if 'df_teknisi' not in st.session_state or st.session_state.df_teknisi is None:
    st.session_state.df_teknisi = load_atau_buat_file_github("daftar_teknisi.csv", df_teknisi_default)

if 'pesan_sukses' not in st.session_state: st.session_state.pesan_sukses = ""
if 'pesan_error' not in st.session_state: st.session_state.pesan_error = ""
if 'status_scan_terakhir' not in st.session_state: st.session_state.status_scan_terakhir = "kosong"

DAFTAR_TEKNISI = st.session_state.df_teknisi['Nama Teknisi'].dropna().tolist() if not st.session_state.df_teknisi.empty else ["PUTRA-SONY"]
DAFTAR_KABEL_OTOMATIS = st.session_state.df_precon.iloc[:, 0].dropna().astype(str).tolist() if st.session_state.df_precon is not None else ["DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR"]

hari_ini_str = datetime.now().strftime("%Y-%m-%d")
df_hari_ini = pd.DataFrame()
if not st.session_state.log_scan_harian.empty:
    df_hari_ini = st.session_state.log_scan_harian[st.session_state.log_scan_harian['Waktu Scan'].astype(str).str.contains(hari_ini_str)]

def proses_scan_sn():
    sn_value = st.session_state.scan_sn_key.strip()
    if sn_value:
        if not df_hari_ini.empty:
            sn_terdata = df_hari_ini['Serial Number (SN)'].astype(str).str.lower().values
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
        simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Auto-Update Scan SN")
        
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' ({nama_barang}) tersimpan!"
        st.session_state.pesan_error = ""
        st.session_state.status_scan_terakhir = "sukses"
        st.session_state.scan_sn_key = ""

# --- SIDEBAR HEADER (Sesuai gambar referensi) ---
st.sidebar.markdown("""
<div style="padding: 5px 0px 15px 0px;">
    <h2 style="color: white; font-size: 18px; font-weight: 700; margin: 0; letter-spacing: 0.5px;">📋 INVENTORY SYSTEM</h2>
    <p style="color: #cbd5e1; font-size: 11px; margin: 2px 0 0 0;">Multi Aplikasi Manajemen</p>
</div>
<div style="color: #94a3b8; font-size: 11px; font-weight: 600; tracking: 1px; margin-bottom: 5px; margin-top: 10px;">APLIKASI UTAMA</div>
""", unsafe_allow_html=True)

menu_options = {
    "pagi": "Scan & Input Pagi",
    "sore": "Laporan Penggunaan Sore",
    "bos": "Laporan Eksekutif Ke Bos",
    "gudang": "Dashboard & Stok Gudang",
    "teknisi": "Histori Sheet Teknisi",
    "pengaturan": "Pengaturan Tim & Material"
}

pilihan_menu = st.sidebar.radio(
    "PILIH HALAMAN APLIKASI:", 
    options=list(menu_options.keys()),
    format_func=lambda x: menu_options[x],
    label_visibility="collapsed"
)

# --- DYNAMIC TOP NAVBAR HEADER (Sesuai gambar referensi) ---
hari_mapping = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
bulan_mapping = {"January": "Januari", "February": "Februari", "March": "Maret", "April": "April", "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus", "September": "September", "October": "Oktober", "November": "November", "December": "Desember"}

now = datetime.now()
hari_indo = hari_mapping.get(now.strftime("%A"), now.strftime("%A"))
bulan_indo = bulan_mapping.get(now.strftime("%B"), now.strftime("%B"))
tgl_format = f"{hari_indo}, {now.strftime('%d')} {bulan_indo} {now.strftime('%Y')}"

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; background-color: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); margin-bottom: 25px;">
    <div style="font-size: 20px; font-weight: 600; color: #1e293b; display: flex; align-items: center; gap: 10px;">
        📂 {menu_options[pilihan_menu]}
    </div>
    <div style="display: flex; gap: 25px; font-size: 13px; color: #64748b; font-weight: 500;">
        <div>📅 {tgl_format}</div>
        <div>👤 User: Admin</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== MENU 1: SCAN & INPUT PAGI ====================
if pilihan_menu == "pagi":
    if st.session_state.pesan_sukses: st.success(st.session_state.pesan_sukses); st.session_state.pesan_sukses = ""
    if st.session_state.pesan_error: st.error(st.session_state.pesan_error); st.session_state.pesan_error = ""

    with st.container(border=True):
        st.markdown("<h4 style='margin-top:0; margin-bottom: 20px; color: #334155; font-weight:600;'>║║ Input Barang Masuk Pagi</h4>", unsafe_allow_html=True)
        
        # Grid 2 Kolom Sesuai Gambar Berkas Contoh
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Serial Number (SN)", placeholder="Tembak barcode SN ke sini...", key="scan_sn_key", on_change=proses_scan_sn)
            st.selectbox("Nama Teknisi", DAFTAR_TEKNISI, key="tek_device")
            
        with col2:
            st.selectbox("Jenis Barang", ["-- Pilih Jenis (Otomatis Mendeteksi SN) --", "ONT Premium", "STB HD Box", "Access Point Outdoor", "Kabel Precon"], key="jenis_barang_dummy")
            st.number_input("Jumlah Unit", min_value=1, value=1, step=1, key="jumlah_unit_dummy")
            
        st.text_area("Keterangan", placeholder="Catatan tambahan atau nomor WO...", key="wo_device", height=80)
        
        if st.button("➕ Tambah Item", type="primary"):
            if st.session_state.scan_sn_key:
                proses_scan_sn()
            else:
                st.toast("Silakan isi atau scan SN terlebih dahulu!", icon="⚠️")

    # --- INPUT KHUSUS KABEL PRECON ---
    with st.container(border=True):
        st.markdown("<h4 style='margin-top:0; margin-bottom: 15px; color: #334155; font-weight:600;'>🧵 Input Log Pengeluaran Kabel Precon</h4>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            tek_kabel = st.selectbox("Pilih Teknisi (Kabel):", DAFTAR_TEKNISI, key="tek_kabel")
            pilihan_kabel = st.selectbox("Ukuran Kabel Precon:", DAFTAR_KABEL_OTOMATIS, key="pilihan_kabel")
        with col_c2:
            jumlah_roll = st.number_input("Jumlah Roll Keluar:", min_value=1, value=1, step=1, key="jumlah_roll")
            wo_kabel = st.text_input("Nomor WO (Kabel):", key="wo_kabel")
            
        if st.button("🧵 Simpan Material Kabel", use_container_width=True):
            for i in range(int(jumlah_roll)):
                label_roll = f"Roll {i+1}"
                ket_final = f"{wo_kabel} ({label_roll})" if wo_kabel else label_roll
                new_row = {
                    'Waktu Scan': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Nama Teknisi': tek_kabel, 
                    'Serial Number (SN)': "-", 'Nama Barang': "Kabel Precon", 'Kabel Precon': pilihan_kabel, 
                    'No WO / Keterangan': ket_final, 'Status Pemasangan Sore': "Belum Dilaporkan ⏳", 
                    'Keterangan Tambahan Sore': "-", 'Stok Dipotong': "Belum"
                }
                st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
            simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Auto-Update Input Kabel")
            st.toast("Kabel sukses dimasukkan!", icon="🧵")
            st.rerun()

    st.markdown("#### 📋 Daftar Input Pagi Hari Ini")
    with st.container(border=True):
        if not df_hari_ini.empty:
            tabel_edit_pagi = st.data_editor(df_hari_ini, num_rows="dynamic", use_container_width=True, key="gudang_editor_pagi")
            if not tabel_edit_pagi.equals(df_hari_ini):
                df_sisanya = st.session_state.log_scan_harian[~st.session_state.log_scan_harian['Waktu Scan'].astype(str).str.contains(hari_ini_str)]
                st.session_state.log_scan_harian = pd.concat([df_sisanya, tabel_edit_pagi], ignore_index=True)
                simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Koreksi Manual Pagi")
                st.rerun()
        else:
            st.info("Belum ada rincian data barang keluar hari ini.")

# ==================== MENU 2: LAPORAN SORE ====================
elif pilihan_menu == "sore":
    with st.container(border=True):
        if not df_hari_ini.empty:
            tabel_edit_sore = st.data_editor(
                df_hari_ini,
                column_config={
                    "Waktu Scan": st.column_config.TextColumn(disabled=True), "Nama Teknisi": st.column_config.TextColumn(disabled=True),
                    "Serial Number (SN)": st.column_config.TextColumn(disabled=True), "Nama Barang": st.column_config.TextColumn(disabled=True),
                    "Kabel Precon": st.column_config.TextColumn(disabled=True), "No WO / Keterangan": st.column_config.TextColumn(disabled=False),
                    "Stok Dipotong": st.column_config.TextColumn(disabled=True),
                    "Status Pemasangan Sore": st.column_config.SelectboxColumn("Status Pemasangan Sore", options=["Belum Dilaporkan ⏳", "Sudah Terinstal ✅", "Belum Terinstal / Retur ❌"], required=True),
                    "Keterangan Tambahan Sore": st.column_config.TextColumn("Keterangan Tambahan Sore")
                },
                use_container_width=True, key="gudang_editor_sore"
            )
            
            if not tabel_edit_sore.equals(df_hari_ini):
                df_sisanya = st.session_state.log_scan_harian[~st.session_state.log_scan_harian['Waktu Scan'].astype(str).str.contains(hari_ini_str)]
                st.session_state.log_scan_harian = pd.concat([df_sisanya, tabel_edit_sore], ignore_index=True)
                simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Koreksi Status Sore")
                st.rerun()
            
            st.markdown("### 🔄 Potong Stok Otomatis")
            if st.button("🔄 Eksekusi Potong Sisa Stok Gudang", type="primary", use_container_width=True):
                jumlah_potong = 0
                for idx, row in st.session_state.log_scan_harian.iterrows():
                    if row['Waktu Scan'].startswith(hari_ini_str) and row['Status Pemasangan Sore'] == "Sudah Terinstal ✅" and row['Stok Dipotong'] == "Belum":
                        if row['Serial Number (SN)'] != "-":
                            if st.session_state.df_device is not None:
                                kondisi = st.session_state.df_device.iloc[:, 0].astype(str).str.lower().str.contains(row['Nama Barang'].lower(), na=False)
                                if kondisi.any():
                                    idx_gudang = st.session_state.df_device[kondisi].index[0]
                                    st.session_state.df_device.at[idx_gudang, st.session_state.df_device.columns[1]] = max(0, st.session_state.df_device.at[idx_gudang, st.session_state.df_device.columns[1]] - 1)
                                    st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                    jumlah_potong += 1
                        elif row['Kabel Precon'] != "-":
                            if st.session_state.df_precon is not None:
                                kondisi = st.session_state.df_precon.iloc[:, 0].astype(str).str.strip() == row['Kabel Precon'].strip()
                                if kondisi.any():
                                    idx_gudang = st.session_state.df_precon[kondisi].index[0]
                                    st.session_state.df_precon.at[idx_gudang, st.session_state.df_precon.columns[1]] = max(0, st.session_state.df_precon.at[idx_gudang, st.session_state.df_precon.columns[1]] - 1)
                                    st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                    jumlah_potong += 1
                                    
                simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Auto-Update Log Sore")
                simpan_file_ke_github("database_device.csv", st.session_state.df_device, "Auto-Potong Stok Device")
                simpan_file_ke_github("database_precon.csv", st.session_state.df_precon, "Auto-Potong Stok Precon")
                st.success(f"🔥 Selesai memotong {jumlah_potong} item dari cloud database!")
                st.rerun()
        else:
            st.warning("Data hari ini masih kosong.")

# ==================== MENU 3: LAPORAN EKSEKUTIF KE BOS ====================
elif pilihan_menu == "bos":
    with st.container(border=True):
        periode = st.selectbox("Filter Periode Analisis:", ["Hari Ini (Daily)", "7 Hari Terakhir", "Semua Riwayat"])
        df_filtered = st.session_state.log_scan_harian.copy()
        
        if periode == "Hari Ini (Daily)":
            df_filtered = df_filtered[df_filtered['Waktu Scan'].astype(str).str.contains(hari_ini_str)]
            
        if not df_filtered.empty:
            t1, t2, t3 = st.columns(3)
            t1.metric("📦 Total Material Keluar", f"{len(df_filtered)} Item")
            t2.metric("✅ Sukses Terpasang", f"{len(df_filtered[df_filtered['Status Pemasangan Sore'] == 'Sudah Terinstal ✅'])} Item")
            t3.metric("❌ Gagal / Retur", f"{len(df_filtered[df_filtered['Status Pemasangan Sore'] == 'Belum Terinstal / Retur ❌'])} Item")
            st.markdown("---")
            st.dataframe(df_filtered, use_container_width=True)
        else:
            st.info("Tidak ditemukan data logistik pada periode terpilih.")

# ==================== MENU 4: DASHBOARD UTAMA ====================
elif pilihan_menu == "gudang":
    with st.container(border=True):
        st.markdown("### 📉 Sisa Stok Cloud Gudang Real-Time")
        if st.button("🔄 Paksa Sinkronisasi Ulang dari File Master SN", type="primary", use_container_width=True):
            st.session_state.df_device = df_device_default
            simpan_file_ke_github("database_device.csv", df_device_default, "Reset Force Sync Master")
            st.rerun()
            
        tab1, tab2 = st.tabs(["📟 Validasi Stok Device", "🧵 Validasi Stok Kabel Precon"])
        with tab1:
            st.dataframe(st.session_state.df_device, use_container_width=True)
        with tab2:
            st.dataframe(st.session_state.df_precon, use_container_width=True)

# ==================== MENU 5: HISTORI SHEET TEKNISI ====================
elif pilihan_menu == "teknisi":
    with st.container(border=True):
        pilihan_tim = st.selectbox("Pilih Teknisi / Tim Lapangan:", DAFTAR_TEKNISI)
        if not st.session_state.log_scan_harian.empty:
            df_fil = st.session_state.log_scan_harian[st.session_state.log_scan_harian['Nama Teknisi'] == pilihan_tim]
            st.dataframe(df_fil, use_container_width=True)

# ==================== MENU 6: PENGATURAN TIM & MATERIAL ====================
elif pilihan_menu == "pengaturan":
    with st.container(border=True):
        t_edit = st.data_editor(st.session_state.df_teknisi, num_rows="dynamic", use_container_width=True)
        if not t_edit.equals(st.session_state.df_teknisi):
            st.session_state.df_teknisi = t_edit
            simpan_file_ke_github("daftar_teknisi.csv", t_edit, "Update List Teknisi")
            st.rerun()
