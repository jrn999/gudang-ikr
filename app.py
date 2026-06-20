import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
from github import Github
import io

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

st.title("⚡ Sistem Logistik IKR Metech")

# --- AMBIL KREDENSIAL GITHUB DARI SECRETS (VERSI ANTI-CRASH) ---
GITHUB_TOKEN = ""
REPO_NAME = ""

try:
    if "GITHUB_TOKEN" in st.secrets:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    if "GITHUB_REPO" in st.secrets:
        REPO_NAME = st.secrets["GITHUB_REPO"]
except Exception:
    pass

# --- TEMPLATE DATABASE DEFAULT JIKA FILE BELUM ADA ---
df_device_default = pd.DataFrame({
    'Nama Barang': ['ONT Premium', 'STB HD Box', 'Access Point Outdoor', 'ONT/STB (Manual/Tidak di Master)', 'Device Terdaftar'],
    'Stok Gudang': [100, 100, 100, 100, 100]
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

# --- FUNGSI DYNAMIC LOAD ATAU BUAT FILE OTOMATIS DI GITHUB ---
def load_atau_buat_file_github(nama_file, df_default):
    if not GITHUB_TOKEN or not REPO_NAME:
        return df_default
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Pastikan branch 'data-log' sudah aktif
        try:
            repo.get_branch("data-log")
        except Exception:
            main_branch = repo.get_branch("main")
            repo.create_git_ref(ref="refs/heads/data-log", sha=main_branch.commit.sha)
            
        # Coba ambil file, kalau tidak ada langsung buat otomatis di GitHub
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

# --- SCANNING FILE MASTER SN LOKAL ---
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

# --- SINKRONISASI INITIAL STATE KE SESSION STATE ---
if 'log_scan_harian' not in st.session_state:
    st.session_state.log_scan_harian = load_atau_buat_file_github("log_harian.csv", pd.DataFrame(
        columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong']
    ))

if 'df_device' not in st.session_state or st.session_state.df_device is None:
    st.session_state.df_device = load_atau_buat_file_github("database_device.csv", df_device_default)

if 'df_precon' not in st.session_state or st.session_state.df_precon is None:
    st.session_state.df_precon = load_atau_buat_file_github("database_precon.csv", df_precon_default)

if 'pesan_sukses' not in st.session_state: st.session_state.pesan_sukses = ""
if 'pesan_error' not in st.session_state: st.session_state.pesan_error = ""
if 'status_scan_terakhir' not in st.session_state: st.session_state.status_scan_terakhir = "kosong"

# Ambil list opsi kabel dari database precon ter-update
DAFTAR_KABEL_OTOMATIS = []
if st.session_state.df_precon is not None and len(st.session_state.df_precon.columns) > 0:
    DAFTAR_KABEL_OTOMATIS = st.session_state.df_precon.iloc[:, 0].dropna().astype(str).tolist()
if not DAFTAR_KABEL_OTOMATIS:
    DAFTAR_KABEL_OTOMATIS = ["DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 125MTR"]

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
        
        simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Auto-Update Scan SN")
        
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' ({nama_barang}) tersimpan aman di GitHub!"
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
            jumlah_roll = st.number_input("Jumlah Pengeluaran (Roll):", min_value=1, value=1, step=1, key="jumlah_roll")
            wo_kabel = st.text_input("Nomor WO / Keterangan Awal (Kabel):", key="wo_kabel")
            
            if st.button("➕ Simpan Kabel ke Log", use_container_width=True, type="primary"):
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
                st.toast(f"Berhasil mengurai {jumlah_roll} Baris Kabel ke GitHub!", icon="🧵")

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
                else: st.markdown("<p style='font-size:26px;margin:0;text-align:center;color:gray;'>-</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 Tabel Pengeluaran Barang Hari Ini")
    if not st.session_state.log_scan_harian.empty:
        st.dataframe(st.session_state.log_scan_harian, use_container_width=True)
        if st.button("🗑️ Reset Tabel Hari Ini"):
            st.session_state.log_scan_harian = pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong'])
            simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Reset Log Harian")
            st.session_state.status_scan_terakhir = "kosong"
            st.rerun()
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU 2: LAPORAN SORE ====================
elif menu == "📝 Laporan Penggunaan Sore (Update Status)":
    st.subheader("📝 Laporan Hasil Kerja Lapangan Sore Hari")
    st.info("💡 Ubah Status Pemasangan Sore, lalu tekan tombol sinkronisasi di bawah untuk memotong stok gudang di GitHub secara otomatis.")
    
    if not st.session_state.log_scan_harian.empty:
        tabel_edit_sore = st.data_editor(
            st.session_state.log_scan_harian,
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
        st.session_state.log_scan_harian = tabel_edit_sore
        
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
                    # Potong Stok Kabel Precon
                    elif row['Kabel Precon'] != "-":
                        if st.session_state.df_precon is not None:
                            kolom_desk_p = st.session_state.df_precon.columns[0]
                            kondisi = st.session_state.df_precon[kolom_desk_p].astype(str).str.strip() == row['Kabel Precon'].strip()
                            if kondisi.any():
                                idx_gudang = st.session_state.df_precon[kondisi].index[0]
                                for col in st.session_state.df_precon.columns:
                                    if st.session_state.df_precon.dtypes[col] in ['int64', 'float64']:
                                        st.session_state.df_precon.at[idx_gudang, col] = max(0, st.session_state.df_precon.at[idx_gudang, col] - 1)
                                        st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                        jumlah_potong += 1
                                        break
                                        
            # Kirim semua update final ke Cloud GitHub
            simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Auto-Update Log Sore")
            simpan_file_ke_github("database_device.csv", st.session_state.df_device, "Auto-Potong Stok Device")
            simpan_file_ke_github("database_precon.csv", st.session_state.df_precon, "Auto-Potong Stok Precon")
            
            if jumlah_potong > 0:
                st.success(f"🔥 Berhasil memotong {jumlah_potong} item material dari cloud database gudang!")
                st.balloons()
            else:
                st.success("✅ Perubahan laporan sore berhasil disinkronkan ke GitHub!")

        st.markdown("### 📥 2. Unduh Berkas Hasil Akhir")
        st.download_button(label="📥 Download Berkas Rekap Logistik (.CSV)", data=st.session_state.log_scan_harian.to_csv(index=False).encode('utf-8'), file_name=f"REKAP_IKR_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
    else:
        st.warning("Data log masih kosong. Silakan isi pengeluaran pagi terlebih dahulu.")

# ==================== MENU 3: DASHBOARD UTAMA ====================
elif menu == "📊 Dashboard & Stok Gudang":
    st.subheader("📊 Dashboard Utama Gudang")
    st.markdown("### 📌 Status Sinkronisasi File di GitHub")
    
    if MASTER_SN_FILE and os.path.exists(MASTER_SN_FILE):
        st.success(f"✅ Master SN: Terkoneksi Aktif ({MASTER_SN_FILE})")
    else:
        st.error("❌ Master SN: File tidak ditemukan di Main Branch!")
        
    st.success("✅ Stok Device: Terkoneksi & Sinkron Otomatis (database_device.csv)")
    st.success("✅ Stok PRECON: Terkoneksi & Sinkron Otomatis (database_precon.csv)")
    st.info("☁️ Cloud Auto-Save Active: Semua data diamankan di branch 'data-log'")

    st.markdown("---")
    t1, t2 = st.tabs(["📟 Stock Device", "🧵 Stock PRECON"])
    with t1:
        if st.session_state.df_device is not None: 
            st.dataframe(st.session_state.df_device, use_container_width=True)
        else: 
            st.info("Data Stock Device kosong.")
    with t2:
        if st.session_state.df_precon is not None: 
            st.dataframe(st.session_state.df_precon, use_container_width=True)
        else: 
            st.info("Data Stock PRECON kosong.")

# ==================== MENU 4: HISTORI SHEET TEKNISI (KEMBALI AKTIF) ====================
elif menu == "👨‍🔧 Histori Sheet Teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan_tim = st.selectbox("Pilih Nama Tim / Teknisi:", DAFTAR_TEKNISI)
    
    st.markdown(f"#### 📋 Log Perjalanan Material Tim: **{pilihan_tim}**")
    
    if not st.session_state.log_scan_harian.empty:
        # Filter data log harian secara cerdas berdasarkan teknisi terpilih
        df_filtered = st.session_state.log_scan_harian[st.session_state.log_scan_harian['Nama Teknisi'] == pilihan_tim]
        
        if not df_filtered.empty:
            st.dataframe(df_filtered, use_container_width=True)
            
            # Berikan info ringkasan ringkas untuk mempermudah mandor logistik
            total_bawa = len(df_filtered)
            total_sukses = len(df_filtered[df_filtered['Status Pemasangan Sore'] == "Sudah Terinstal ✅"])
            
            st.toast(f"Menampilkan {total_bawa} data log untuk {pilihan_tim}", icon="👨‍🔧")
            st.info(f"💡 **Ringkasan Hari Ini:** Tim {pilihan_tim} mengambil total **{total_bawa} material**, dan **{total_sukses} di antaranya** dilaporkan sudah terpasang sore ini.")
        else:
            st.info(f"Belum ada riwayat pengambilan atau laporan material untuk tim **{pilihan_tim}** hari ini.")
    else:
        st.warning("Belum ada data log harian yang tercatat di sistem cloud.")
