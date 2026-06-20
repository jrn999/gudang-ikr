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

# --- DETEKSI FILE SUPER PINTAR (Mendukung Excel .xlsx maupun Split .csv) ---
semua_file = os.listdir('.')

# 1. Scanning File MASTER SN (.csv)
MASTER_SN_FILE = None
for f in semua_file:
    if f.endswith('.csv') and ("MASTER" in f.upper() or "SN" in f.upper()):
        MASTER_SN_FILE = f
        break
if not MASTER_SN_FILE:
    for f in semua_file:
        if f.endswith('.csv') and "DEVICE" not in f.upper() and "PRECON" not in f.upper():
            MASTER_SN_FILE = f
            break
if not MASTER_SN_FILE: MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"

# 2. Scanning Database Stock Device (Bisa berupa CSV terpisah atau Excel)
DEVICE_FILE = None
is_device_csv = False
for f in semua_file:
    if "DEVICE" in f.upper():
        DEVICE_FILE = f
        if f.endswith('.csv'): is_device_csv = True
        break
if not DEVICE_FILE:
    for f in semua_file:
        if f.endswith('.xlsx'): DEVICE_FILE = f; break

# 3. Scanning Database Stock Precon (Bisa berupa CSV terpisah atau Excel)
PRECON_FILE = None
is_precon_csv = False
for f in semua_file:
    if "PRECON" in f.upper():
        PRECON_FILE = f
        if f.endswith('.csv'): is_precon_csv = True
        break
if not PRECON_FILE:
    for f in semua_file:
        if f.endswith('.xlsx'): PRECON_FILE = f; break

# --- FUNGSI LOADING DATA RESILIEN ---
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

def load_data_gudang(nama_file, is_csv, sheet_name):
    if nama_file and os.path.exists(nama_file):
        try:
            if is_csv or nama_file.endswith('.csv'):
                df = pd.read_csv(nama_file)
            else:
                df = pd.read_excel(nama_file, sheet_name=sheet_name, engine='openpyxl')
            df.columns = df.columns.str.strip()
            return df
        except:
            return None
    return None

# --- DEKLARASI SESSION STATE (DATABASE APLIKASI) ---
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

# Sinkronisasi Data Gudang ke Memori Aplikasi
if 'df_device' not in st.session_state or st.session_state.df_device is None:
    st.session_state.df_device = load_data_gudang(DEVICE_FILE, is_device_csv, "Stock Device")
if 'df_precon' not in st.session_state or st.session_state.df_precon is None:
    st.session_state.df_precon = load_data_gudang(PRECON_FILE, is_precon_csv, "Stock PRECON")

df_master = load_master_sn(MASTER_SN_FILE)

# --- MENYUSUN DAFTAR OPSI KABEL ---
DAFTAR_KABEL_OTOMATIS = []
if st.session_state.df_precon is not None:
    kolom_deskripsi = None
    for col in st.session_state.df_precon.columns:
        if 'DESC' in str(col).upper() or 'NAMA' in str(col).upper() or 'MATERIAL' in str(col).upper():
            kolom_deskripsi = col
            break
    if kolom_deskripsi is None and len(st.session_state.df_precon.columns) > 0:
        kolom_deskripsi = st.session_state.df_precon.columns[0]
        
    if kolom_deskripsi in st.session_state.df_precon.columns:
        list_kabel = st.session_state.df_precon[kolom_deskripsi].dropna().astype(str).tolist()
        DAFTAR_KABEL_OTOMATIS = [kabel.strip() for kabel in list_kabel if kabel.strip()]

if not DAFTAR_KABEL_OTOMATIS:
    DAFTAR_KABEL_OTOMATIS = ["DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 125MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 175MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 225MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 300MTR"]

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

# --- SIDEBAR MENU ---
st.sidebar.markdown("### 📊 NAVIGATION MENU")
menu = st.sidebar.radio(
    "PILIH HALAMAN APLIKASI:", 
    ["✍️ Scan & Input Pagi (Pengeluaran)", "📝 Laporan Penggunaan Sore (Update Status)", "📊 Dashboard & Stok Gudang", "👨‍🔧 Histori Sheet Teknisi"]
)

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
            
            # FITUR BARU: Input Jumlah Roll untuk diuraikan otomatis
            jumlah_roll = st.number_input("Jumlah Pengeluaran (Roll):", min_value=1, value=1, step=1, key="jumlah_roll")
            
            wo_kabel = st.text_input("Nomor WO / Keterangan Awal (Kabel):", key="wo_kabel")
            
            if st.button("➕ Simpan Kabel ke Log", use_container_width=True, type="primary"):
                # Proses looping pemecah baris (Urai per rol)
                for i in range(int(jumlah_roll)):
                    label_roll = f"Roll {i+1}"
                    ket_final = f"{wo_kabel} ({label_roll})" if wo_kabel else label_roll
                    
                    new_row = {
                        'Waktu Scan': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                        'Nama Teknisi': tek_kabel, 
                        'Serial Number (SN)': "-", 
                        'Nama Barang': "Kabel Precon",
                        'Kabel Precon': pilihan_kabel, 
                        'No WO / Keterangan': ket_final, 
                        'Status Pemasangan Sore': "Belum Dilaporkan ⏳", 
                        'Keterangan Tambahan Sore': "-", 
                        'Stok Dipotong': "Belum"
                    }
                    st.session_state.log_scan_harian = pd.concat([st.session_state.log_scan_harian, pd.DataFrame([new_row])], ignore_index=True)
                st.toast(f"Berhasil mengurai {jumlah_roll} Baris Kabel ke tabel!", icon="🧵")

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
        if st.button("🗑️ Reset Tabel Hari Ini"):
            st.session_state.log_scan_harian = pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong'])
            st.session_state.status_scan_terakhir = "kosong"
            st.rerun()
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU 2: LAPORAN SORE ====================
elif menu == "📝 Laporan Penggunaan Sore (Update Status)":
    st.subheader("📝 Laporan Hasil Kerja Lapangan Sore Hari")
    
    if not st.session_state.log_scan_harian.empty:
        # Menggunakan SelectboxColumn (Solusi perbaikan Error image_591204)
        tabel_edit_sore = st.data_editor(
            st.session_state.log_scan_harian,
            column_config={
                "Waktu Scan": st.column_config.TextColumn(disabled=True), 
                "Nama Teknisi": st.column_config.TextColumn(disabled=True),
                "Serial Number (SN)": st.column_config.TextColumn(disabled=True), 
                "Nama Barang": st.column_config.TextColumn(disabled=True),
                "Kabel Precon": st.column_config.TextColumn(disabled=True), 
                "No WO / Keterangan": st.column_config.TextColumn(disabled=False), # DIBUKA agar bisa ganti ukuran/WO per rol!
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
        
        # --- PROSES EKSEKUSI POTONG STOK ---
        st.markdown("### 🔄 1. Eksekusi Potong Stok Gudang")
        if st.button("🔄 Proses Sinkronisasi & Potong Stok Otomatis", type="secondary", use_container_width=True):
            jumlah_potong = 0
            for idx, row in st.session_state.log_scan_harian.iterrows():
                if row['Status Pemasangan Sore'] == "Sudah Terinstal ✅" and row['Stok Dipotong'] == "Belum":
                    # Potong Stok Device
                    if row['Serial Number (SN)'] != "-":
                        if st.session_state.df_device is not None:
                            kondisi = st.session_state.df_device.iloc[:, 0].astype(str).str.lower().str.contains(row['Nama Barang'].lower(), na=False)
                            if kondisi.any():
                                idx_gudang = st.session_state.df_device[kondisi].index[0]
                                for col in st.session_state.df_device.columns:
                                    if st.session_state.df_device.dtypes[col] in ['int64', 'float64']:
                                        st.session_state.df_device.at[idx_gudang, col] = max(0, st.session_state.df_device.at[idx_gudang, col] - 1)
                                        st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                        jumlah_potong += 1
                                        break
                    # Potong Stok Kabel Precon (Berjalan per baris roll yang sukses)
                    elif row['Kabel Precon'] != "-":
                        if st.session_state.df_precon is not None:
                            kolom_desk_p = st.session_state.df_precon.columns[0]
                            for c in st.session_state.df_precon.columns:
                                if 'DESC' in str(c).upper() or 'MATERIAL' in str(c).upper(): kolom_desk_p = c; break
                            kondisi = st.session_state.df_precon[kolom_desk_p].astype(str).str.strip() == row['Kabel Precon'].strip()
                            if kondisi.any():
                                idx_gudang = st.session_state.df_precon[kondisi].index[0]
                                for col in st.session_state.df_precon.columns:
                                    if st.session_state.df_precon.dtypes[col] in ['int64', 'float64']:
                                        st.session_state.df_precon.at[idx_gudang, col] = max(0, st.session_state.df_precon.at[idx_gudang, col] - 1)
                                        st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                        jumlah_potong += 1
                                        break
            if jumlah_potong > 0:
                st.success(f"🔥 Berhasil memotong {jumlah_potong} item material dari database internal gudang!")
                st.balloons()
            else:
                st.info("Tidak ada item baru dengan status terpasang yang perlu dipotong.")

        st.markdown("### 📥 2. Unduh Berkas Hasil Akhir")
        st.download_button(label="📥 Download Berkas Rekap Logistik (.CSV)", data=st.session_state.log_scan_harian.to_csv(index=False).encode('utf-8'), file_name=f"REKAP_IKR_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
    else:
        st.warning("Data log masih kosong. Silakan isi pengeluaran pagi terlebih dahulu.")

# ==================== MENU 3: DASHBOARD UTAMA ====================
elif menu == "📊 Dashboard & Stok Gudang":
    st.subheader("📊 Dashboard Utama Gudang")
    st.markdown("### 📌 Status Sinkronisasi File di GitHub")
    
    if MASTER_SN_FILE and os.path.exists(MASTER_SN_FILE):
        st.success(f"✅ Master SN: Terkoneksi ({MASTER_SN_FILE})")
    else:
        st.error("❌ Master SN: File tidak ditemukan!")
        
    if DEVICE_FILE and os.path.exists(DEVICE_FILE):
        st.success(f"✅ Stok Device: Terkoneksi Aktif ({DEVICE_FILE})")
    else:
        st.error("❌ Stok Device: File tidak ditemukan di GitHub!")
        
    if PRECON_FILE and os.path.exists(PRECON_FILE):
        st.success(f"✅ Stok Precon: Terkoneksi Aktif ({PRECON_FILE})")
    else:
        st.error("❌ Stok Precon: File tidak ditemukan di GitHub!")

    st.markdown("---")
    t1, t2 = st.tabs(["📟 Stock Device", "🧵 Stock PRECON"])
    with t1:
        if st.session_state.df_device is not None: st.dataframe(st.session_state.df_device, use_container_width=True)
        else: st.info("Data sheet 'Stock Device' belum terbaca.")
    with t2:
        if st.session_state.df_precon is not None: st.dataframe(st.session_state.df_precon, use_container_width=True)
        else: st.info("Data sheet 'Stock PRECON' belum terbaca.")

# ==================== MENU 4: HISTORI SHEET TEKNISI ====================
elif menu == "👨‍🔧 Histori Sheet Teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan = st.selectbox("Pilih Nama Tim:", DAFTAR_TEKNISI)
    # Gunakan file deteksi dinamis untuk backup pembacaan teknisi
    FILE_SAMPEL = DEVICE_FILE if DEVICE_FILE else PRECON_FILE
    if FILE_SAMPEL and FILE_SAMPEL.endswith('.xlsx'):
        df_tek = load_data_gudang(FILE_SAMPEL, False, pilihan)
        if df_tek is not None: st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
        else: st.info(f"Sheet bernama '{pilihan}' tidak ditemukan di dalam file Excel.")
    else:
        st.info("Fitur histori sheet dinonaktifkan karena Anda menggunakan database tipe .CSV terpisah.")
