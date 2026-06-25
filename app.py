import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
from github import Github
import io

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

st.title("⚡ Sistem Logistik IKR Metech")

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

# --- FUNGSI DYNAMIC LOAD ATAU BUAT FILE OTOMATIS DI GITHUB ---
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

# --- SINKRONISASI DATABASES KE SESSION STATE ---
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

# Ambil List Dinamis untuk Dropdown Aplikasi
DAFTAR_TEKNISI = st.session_state.df_teknisi['Nama Teknisi'].dropna().tolist() if not st.session_state.df_teknisi.empty else ["PUTRA-SONY"]

DAFTAR_KABEL_OTOMATIS = []
if st.session_state.df_precon is not None and len(st.session_state.df_precon.columns) > 0:
    DAFTAR_KABEL_OTOMATIS = st.session_state.df_precon.iloc[:, 0].dropna().astype(str).tolist()
if not DAFTAR_KABEL_OTOMATIS:
    DAFTAR_KABEL_OTOMATIS = ["DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR"]

# Filter Otomatis Data khusus HARI INI
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
        
        st.session_state.pesan_sukses = f"🎉 BERHASIL: SN '{sn_value}' ({nama_barang}) tersimpan aman!"
        st.session_state.pesan_error = ""
        st.session_state.status_scan_terakhir = "sukses"
        st.session_state.scan_sn_key = ""

# --- MAP NAVIGATION MENU (ANTI BUG EMOJI) ---
st.sidebar.markdown("### 📊 NAVIGATION MENU")
menu_options = {
    "pagi": "✍️ Scan & Input Pagi (Pengeluaran)",
    "sore": "📝 Laporan Penggunaan Sore (Update Status)",
    "bos": "📊 Laporan Eksekutif Ke Bos",
    "gudang": "📉 Dashboard & Stok Gudang",
    "teknisi": "👨‍🔧 Histori Sheet Teknisi",
    "pengaturan": "⚙️ Pengaturan Tim & Material"
}

pilihan_menu = st.sidebar.radio(
    "PILIH HALAMAN APLIKASI:", 
    options=list(menu_options.keys()),
    format_func=lambda x: menu_options[x]
)

# ==================== MENU 1: SCAN & INPUT PAGI ====================
if pilihan_menu == "pagi":
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
                st.toast(f"Berhasil menambahkan {jumlah_roll} Baris Kabel!", icon="🧵")
                st.rerun()

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
    st.markdown("#### 📋 Tabel Pengeluaran Barang (Hari Ini)")
    
    if not df_hari_ini.empty:
        tabel_edit_pagi = st.data_editor(df_hari_ini, num_rows="dynamic", use_container_width=True, key="gudang_editor_pagi")
        
        if not tabel_edit_pagi.equals(df_hari_ini):
            df_sisanya = st.session_state.log_scan_harian[~st.session_state.log_scan_harian['Waktu Scan'].astype(str).str.contains(hari_ini_str)]
            st.session_state.log_scan_harian = pd.concat([df_sisanya, tabel_edit_pagi], ignore_index=True)
            simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Koreksi Manual Pagi")
            st.toast("Perubahan data tersimpan! 🔄")
            st.rerun()
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU 2: LAPORAN SORE (ADMIN ONLY & FLEKSIBEL TANGGAL) ====================
elif pilihan_menu == "sore":
    st.subheader("📝 Update Status Instalasi Lapangan (Khusus Admin)")
    
    # --- 1. FITUR KEAMANAN ADMIN ---
    password_admin = st.text_input("🔑 Masukkan Password Admin untuk membuka akses:", type="password")
    PASSWORD_BENAR = "admin123" # GANTI password ini sesuai keinginan Anda
    
    if password_admin == PASSWORD_BENAR:
        st.success("✅ Akses Terbuka! Anda sekarang dapat mengubah status pemasangan kapan saja.")
        
        # --- 2. FILTER DATA (TIDAK TERBATAS HARI INI) ---
        # Memberikan pilihan untuk menampilkan data yang masih menggantung atau semua data historis
        filter_tampil = st.radio(
            "Pilih Data yang Ditampilkan:", 
            ["Tampilkan Hanya Status 'Belum Dilaporkan ⏳'", "Tampilkan Semua Riwayat Logistik"],
            horizontal=True
        )
        
        if filter_tampil == "Tampilkan Hanya Status 'Belum Dilaporkan ⏳'":
            df_target = st.session_state.log_scan_harian[st.session_state.log_scan_harian['Status Pemasangan Sore'] == "Belum Dilaporkan ⏳"]
        else:
            df_target = st.session_state.log_scan_harian

        if not df_target.empty:
            tabel_edit_sore = st.data_editor(
                df_target,
                column_config={
                    "Waktu Scan": st.column_config.TextColumn(disabled=True), 
                    "Nama Teknisi": st.column_config.TextColumn(disabled=True),
                    "Serial Number (SN)": st.column_config.TextColumn(disabled=True), 
                    "Nama Barang": st.column_config.TextColumn(disabled=True),
                    "Kabel Precon": st.column_config.TextColumn(disabled=True), 
                    "No WO / Keterangan": st.column_config.TextColumn(disabled=False),
                    "Stok Dipotong": st.column_config.TextColumn(disabled=True),
                    "Status Pemasangan Sore": st.column_config.SelectboxColumn("Status Pemasangan Sore", options=["Belum Dilaporkan ⏳", "Sudah Terinstal ✅", "Belum Terinstal / Retur ❌"], required=True),
                    "Keterangan Tambahan Sore": st.column_config.TextColumn("Keterangan Tambahan Sore")
                },
                use_container_width=True, key="gudang_editor_admin"
            )
            
            # --- 3. SIMPAN PERUBAHAN TEPAT DI BARIS YANG DIEDIT ---
            if not tabel_edit_sore.equals(df_target):
                # .update() akan memperbarui data master berdasarkan nomor index baris (kapanpun tanggalnya)
                st.session_state.log_scan_harian.update(tabel_edit_sore)
                simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Admin: Update Status Koreksi")
                st.rerun()
            
            st.markdown("### 🔄 1. Eksekusi Potong Stok Gudang")
            if st.button("🔄 Proses Sinkronisasi & Potong Stok Otomatis", type="secondary", use_container_width=True):
                jumlah_potong = 0
                for idx, row in st.session_state.log_scan_harian.iterrows():
                    # LOGIKA BARU: Menghapus syarat hari ini. Semua yang statusnya "Sudah Terinstal" & belum dipotong akan diproses.
                    if row['Status Pemasangan Sore'] == "Sudah Terinstal ✅" and row['Stok Dipotong'] == "Belum":
                        if row['Serial Number (SN)'] != "-":
                            if st.session_state.df_device is not None:
                                kondisi = st.session_state.df_device.iloc[:, 0].astype(str).str.lower().str.contains(row['Nama Barang'].lower(), na=False)
                                if kondisi.any():
                                    idx_gudang = st.session_state.df_device[kondisi].index[0]
                                    col_target = st.session_state.df_device.columns[1]
                                    st.session_state.df_device.at[idx_gudang, col_target] = max(0, st.session_state.df_device.at[idx_gudang, col_target] - 1)
                                    st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                    jumlah_potong += 1
                        elif row['Kabel Precon'] != "-":
                            if st.session_state.df_precon is not None:
                                kolom_desk_p = st.session_state.df_precon.columns[0]
                                kondisi = st.session_state.df_precon[kolom_desk_p].astype(str).str.strip() == row['Kabel Precon'].strip()
                                if kondisi.any():
                                    idx_gudang = st.session_state.df_precon[kondisi].index[0]
                                    col_target = st.session_state.df_precon.columns[1]
                                    st.session_state.df_precon.at[idx_gudang, col_target] = max(0, st.session_state.df_precon.at[idx_gudang, col_target] - 1)
                                    st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                    jumlah_potong += 1
                                        
                simpan_file_ke_github("log_harian.csv", st.session_state.log_scan_harian, "Auto-Update Log Sinkron")
                simpan_file_ke_github("database_device.csv", st.session_state.df_device, "Auto-Potong Stok Device")
                simpan_file_ke_github("database_precon.csv", st.session_state.df_precon, "Auto-Potong Stok Precon")
                
                if jumlah_potong > 0:
                    st.success(f"🔥 Berhasil memotong {jumlah_potong} item material historis/baru dari cloud database gudang!")
                    st.balloons()
                    st.rerun()
                else:
                    st.info("✅ Semua material yang 'Sudah Terinstal' sudah terpotong stoknya.")
                    
            # --- DOWNLOAD EXCEL ---
            st.markdown("### 📥 2. Unduh Data Ditampilkan (.xlsx)")
            buffer_sore = io.BytesIO()
            with pd.ExcelWriter(buffer_sore, engine='openpyxl') as writer:
                df_target.to_excel(writer, index=False, sheet_name='Rekap Status')
            st.download_button(
                label="📥 Download Excel File", 
                data=buffer_sore.getvalue(), 
                file_name=f"REKAP_STATUS_{datetime.now().strftime('%Y-%m-%d')}.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True
            )
        else:
            st.info("🎉 Bagus! Semua material sudah memiliki status pemasangan, tidak ada data yang menggantung.")
    
    elif password_admin != "":
        st.error("❌ Password salah! Akses ditolak.")
    else:
        st.warning("🔒 Silakan masukkan password admin di atas untuk membuka gembok tabel.")
# ==================== MENU 3: LAPORAN EKSEKUTIF KE BOS ====================
elif pilihan_menu == "bos":
    st.subheader("📊 Pusat Laporan & Analisa Distribusi Material")
    periode = st.selectbox("Pilih Periode Laporan:", ["Hari Ini (Daily)", "7 Hari Terakhir (Weekly)", "30 Hari Terakhir (Monthly)", "Semua Riwayat (All Time)"])
    
    df_history = st.session_state.log_scan_harian.copy()
    df_history['Waktu Scan DT'] = pd.to_datetime(df_history['Waktu Scan'], errors='coerce')
    sekarang = datetime.now()
    
    if periode == "Hari Ini (Daily)":
        df_filtered = df_history[df_history['Waktu Scan'].astype(str).str.contains(hari_ini_str)]
    elif periode == "7 Hari Terakhir (Weekly)":
        tgl_batas = sekarang - timedelta(days=7)
        df_filtered = df_history[df_history['Waktu Scan DT'] >= tgl_batas]
    elif periode == "30 Hari Terakhir (Monthly)":
        tgl_batas = sekarang - timedelta(days=30)
        df_filtered = df_history[df_history['Waktu Scan DT'] >= tgl_batas]
    else:
        df_filtered = df_history

    if not df_filtered.empty:
        total_out = len(df_filtered)
        total_installed = len(df_filtered[df_filtered['Status Pemasangan Sore'] == "Sudah Terinstal ✅"])
        total_retur = len(df_filtered[df_filtered['Status Pemasangan Sore'] == "Belum Terinstal / Retur ❌"])
        total_pending = len(df_filtered[df_filtered['Status Pemasangan Sore'] == "Belum Dilaporkan ⏳"])
        success_rate = (total_installed / total_out * 100) if total_out > 0 else 0
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("📦 Total Material Keluar", f"{total_out} Item")
        m2.metric("✅ Sukses Terpasang", f"{total_installed} Item")
        m3.metric("❌ Retur / Gagal", f"{total_retur} Item")
        m4.metric("⏳ Pending / Belum Lapor", f"{total_pending} Item")
        m5.metric("📈 Rasio Keberhasilan", f"{success_rate:.1f}%")
        
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**📈 Produktivitas Tim Teknisi (Instalasi Sukses):**")
            df_sukses = df_filtered[df_filtered['Status Pemasangan Sore'] == "Sudah Terinstal ✅"]
            if not df_sukses.empty: 
                df_chart1 = df_sukses['Nama Teknisi'].value_counts().reset_index()
                df_chart1.columns = ['Nama Teknisi', 'Jumlah']
                st.bar_chart(df_chart1, x='Nama Teknisi', y='Jumlah')
            else: 
                st.info("💡 Belum ada data instalasi sukses untuk periode ini.")
        with g2:
            st.markdown("**📦 Jenis Material Paling Banyak Keluar:**")
            df_calc = df_filtered.copy()
            df_calc['Item Laporan'] = df_calc.apply(lambda r: r['Kabel Precon'] if str(r['Kabel Precon']) != "-" else r['Nama Barang'], axis=1)
            df_chart2 = df_calc['Item Laporan'].value_counts().reset_index()
            df_chart2.columns = ['Nama Material', 'Jumlah']
            st.bar_chart(df_chart2, x='Nama Material', y='Jumlah')
            
        st.markdown("---")
        st.markdown(f"#### 📋 Tabel Rincian Data Logistik - Periode {periode}")
        tabel_tampil = df_filtered.drop(columns=['Waktu Scan DT'], errors='ignore')
        st.dataframe(tabel_tampil, use_container_width=True)
        
        # --- PROSES EXPORT BIAR JADI EXCEL ASLI .XLSX ---
        buffer_bos = io.BytesIO()
        with pd.ExcelWriter(buffer_bos, engine='openpyxl') as writer:
            tabel_tampil.to_excel(writer, index=False, sheet_name='Laporan Ke Bos')
            
        st.download_button(
            label=f"📥 Download Berkas Laporan Eksekutif ({periode}) Format Excel Asli (.xlsx)",
            data=buffer_bos.getvalue(),
            file_name=f"LAPORAN_BOS_{periode.replace(' ', '_')}_{hari_ini_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.warning("Tidak ditemukan data logistik pada periode ini.")

# ==================== MENU 4: DASHBOARD UTAMA ====================
elif pilihan_menu == "gudang":
    st.subheader("📉 Dashboard Utama & Kontrol Sisa Stok")
    
    if st.button("🔄 Sinkronkan & Timpa Stok Awal dari Master SN", type="primary", use_container_width=True):
        if not df_master.empty and 'Nama_Barang' in df_master.columns:
            st.session_state.df_device = df_device_default
            simpan_file_ke_github("database_device.csv", df_device_default, "Force Sync Reset dari Master SN")
            st.success("🔥 SUKSES! Stok awal diatur ulang berdasarkan Master SN!")
            st.rerun()

    t1, t2 = st.tabs(["📟 Stock Device (Hitungan Master SN)", "🧵 Stock PRECON"])
    with t1:
        if st.session_state.df_device is not None: st.dataframe(st.session_state.df_device, use_container_width=True)
    with t2:
        if st.session_state.df_precon is not None: st.dataframe(st.session_state.df_precon, use_container_width=True)

# ==================== MENU 5: HISTORI SHEET TEKNISI ====================
elif pilihan_menu == "teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan_tim = st.selectbox("Pilih Nama Tim / Teknisi:", DAFTAR_TEKNISI)
    
    if not st.session_state.log_scan_harian.empty:
        df_filtered = st.session_state.log_scan_harian[st.session_state.log_scan_harian['Nama Teknisi'] == pilihan_tim]
        if not df_filtered.empty: st.dataframe(df_filtered, use_container_width=True)
        else: st.info(f"Belum ada riwayat untuk tim **{pilihan_tim}**.")
    else:
        st.info("Belum ada data log harian.")

# ==================== MENU 6: PENGATURAN TIM & MATERIAL ====================
elif pilihan_menu == "pengaturan":
    st.subheader("⚙️ Control Panel - Pengaturan Tim & Material")
    tab_tim, tab_kabel = st.tabs(["👨‍🔧 Kelola Daftar Tim / Teknisi", "🧵 Kelola Ukuran & Stok Awal Kabel"])
    
    with tab_tim:
        st.markdown("#### 📋 Tambah atau Hapus Tim Teknisi")
        nama_baru = st.text_input("Ketik Nama Tim Baru:", key="input_nama_baru").strip().upper()
        if st.button("➕ Daftarkan Tim Baru", use_container_width=True):
            if nama_baru and nama_baru not in st.session_state.df_teknisi['Nama Teknisi'].values:
                new_tk = pd.DataFrame([{'Nama Teknisi': nama_baru}])
                st.session_state.df_teknisi = pd.concat([st.session_state.df_teknisi, new_tk], ignore_index=True)
                simpan_file_ke_github("daftar_teknisi.csv", st.session_state.df_teknisi, f"Tambah {nama_baru}")
                st.success(f"Berhasil menambahkan tim {nama_baru}!")
                st.rerun()
        
        tabel_tim_edit = st.data_editor(st.session_state.df_teknisi, num_rows="dynamic", use_container_width=True)
        if not tabel_tim_edit.equals(st.session_state.df_teknisi):
            st.session_state.df_teknisi = tabel_tim_edit
            simpan_file_ke_github("daftar_teknisi.csv", st.session_state.df_teknisi, "Update Teknisi")
            st.rerun()

    with tab_kabel:
        st.markdown("#### 📊 Atur Ulang Stok & Jenis Kabel Precon Gudang")
        tabel_kabel_edit = st.data_editor(st.session_state.df_precon, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Simpan Perubahan Data Kabel", type="primary", use_container_width=True):
            st.session_state.df_precon = tabel_kabel_edit
            simpan_file_ke_github("database_precon.csv", st.session_state.df_precon, "Update Kabel")
            st.success("🔥 Data Berhasil Diperbarui!")
