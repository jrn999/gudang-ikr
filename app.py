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

# --- DETEKSI FILE DI GITHUB (OTOMATIS) ---
semua_file = os.listdir('.')

MASTER_SN_FILE = "Untitled spreadsheet - 1. MASTER_SN.csv"
for f in semua_file:
    if "MASTER_SN" in f:
        MASTER_SN_FILE = f

EXCEL_FILE = "MATERIAL IKR [ KEBUTUHAN WO HARIAN ].xlsx"
for f in semua_file:
    if "MATERIAL IKR" in f and f.endswith('.xlsx'):
        EXCEL_FILE = f

# --- DEKLARASI SESSION STATE (DATABASE INTERN APLIKASI) ---
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

# --- FUNGSI LOADING DATA ---
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

def load_excel_sheet(sheet_name):
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, engine='openpyxl')
            df.columns = df.columns.str.strip()
            return df
        except:
            return None
    return None

# --- MENYIMPAN DATABASE STOK DI SESSION STATE AGAR BISA DIPOTONG OTOMATIS ---
if 'df_device' not in st.session_state:
    st.session_state.df_device = load_excel_sheet("Stock Device")
if 'df_precon' not in st.session_state:
    st.session_state.df_precon = load_excel_sheet("Stock PRECON")

df_master = load_master_sn()

# --- PROSES DAFTAR KABEL ---
DAFTAR_KABEL_OTOMATIS = []
if st.session_state.df_precon is not None and 'Description' in st.session_state.df_precon.columns:
    list_kabel = st.session_state.df_precon['Description'].dropna().astype(str).tolist()
    DAFTAR_KABEL_OTOMATIS = [kabel.strip() for kabel in list_kabel if "CABLE" in kabel or "MTR" in kabel]

if not DAFTAR_KABEL_OTOMATIS:
    DAFTAR_KABEL_OTOMATIS = ["DTFIBER - CABLE PRECON SC/UPC-SC/APC - 75MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 125MTR", "DTFIBER - CABLE PRECON SC/UPC-SC/APC - 175MTR"]

DAFTAR_TEKNISI = ["PUTRA-SONY", "RIYAN-RIYADI", "NADI-PARI", "ARIF-YASRIL", "NOVANS-GOBY", "PERI-ROBIN", "TEDI-DODI", "REFKY-DODI", "RAHMAN-AGUS", "IDDO-NAUFAL"]

# --- AUTOMATIC CALLBACK SCAN SN ---
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
    st.write("Masukkan kredensial Bot Telegram Grup Anda di sini:")
    bot_token = st.text_input("Bot Token ID:", value="", type="password", help="Contoh: 123456:ABCdefGhIJK...")
    chat_id = st.text_input("Telegram Chat ID / Group ID:", value="", help="Contoh: -100123456789")

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
        if st.button("🗑️ Kosongkan Tabel Pagi (Reset)"):
            st.session_state.log_scan_harian = pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong'])
            st.session_state.status_scan_terakhir = "kosong"
            st.rerun()
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU 2: LAPORAN SORE + AUTO POTONG + TELEGRAM ====================
elif menu == "📝 Laporan Penggunaan Sore (Update Status)":
    st.subheader("📝 Laporan Hasil Kerja Lapangan Sore Hari")
    st.info("💡 CARA PENGGUNAAN: Klik ganda pada kolom 'Status Pemasangan Sore' untuk update status sesuai Telegram harian Anda.")
    
    if not st.session_state.log_scan_harian.empty:
        tabel_edit_sore = st.data_editor(
            st.session_state.log_scan_harian,
            column_config={
                "Waktu Scan": st.column_config.TextColumn(disabled=True), "Nama Teknisi": st.column_config.TextColumn(disabled=True),
                "Serial Number (SN)": st.column_config.TextColumn(disabled=True), "Nama Barang": st.column_config.TextColumn(disabled=True),
                "Kabel Precon": st.column_config.TextColumn(disabled=True), "No WO / Keterangan": st.column_config.TextColumn(disabled=True),
                "Stok Dipotong": st.column_config.TextColumn(disabled=True),
                "Status Pemasangan Sore": st.column_config.SelectColumn("Status Pemasangan Sore", options=["Belum Dilaporkan ⏳", "Sudah Terinstal ✅", "Belum Terinstal / Retur ❌"], required=True),
                "Keterangan Tambahan Sore": st.column_config.TextColumn("Keterangan Tambahan Sore (Ketik Sini)")
            },
            use_container_width=True, key="gudang_editor_sore"
        )
        st.session_state.log_scan_harian = tabel_edit_sore
        
        # --- TOMBOL 1: AUTO POTONG STOK ---
        st.markdown("### 🔄 1. Eksekusi Potong Stok Gudang")
        if st.button("🔄 Proses Sinkronisasi & Potong Stok Otomatis", type="secondary", use_container_width=True):
            jumlah_potong = 0
            for idx, row in st.session_state.log_scan_harian.iterrows():
                if row['Status Pemasangan Sore'] == "Sudah Terinstal ✅" and row['Stok Dipotong'] == "Belum":
                    # Potong Device
                    if row['Serial Number (SN)'] != "-":
                        if st.session_state.df_device is not None:
                            # Cari baris yang nama barangnya mirip/sesuai
                            kondisi = st.session_state.df_device.iloc[:, 0].astype(str).str.lower().str.contains(row['Nama Barang'].lower(), na=False)
                            if kondisi.any():
                                idx_gudang = st.session_state.df_device[kondisi].index[0]
                                # Cari kolom numerik/stok (kolom indeks ke-1 atau ke-2 biasanya qty)
                                for col in st.session_state.df_device.columns:
                                    if st.session_state.df_device.dtypes[col] in ['int64', 'float64']:
                                        st.session_state.df_device.at[idx_gudang, col] = max(0, st.session_state.df_device.at[idx_gudang, col] - 1)
                                        st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                        jumlah_potong += 1
                                        break
                    # Potong Kabel Precon
                    elif row['Kabel Precon'] != "-":
                        if st.session_state.df_precon is not None and 'Description' in st.session_state.df_precon.columns:
                            kondisi = st.session_state.df_precon['Description'].astype(str).str.strip() == row['Kabel Precon'].strip()
                            if kondisi.any():
                                idx_gudang = st.session_state.df_precon[kondisi].index[0]
                                for col in st.session_state.df_precon.columns:
                                    if st.session_state.df_precon.dtypes[col] in ['int64', 'float64']:
                                        st.session_state.df_precon.at[idx_gudang, col] = max(0, st.session_state.df_precon.at[idx_gudang, col] - 1)
                                        st.session_state.log_scan_harian.at[idx, 'Stok Dipotong'] = "Berhasil Terpotong 📉"
                                        jumlah_potong += 1
                                        break
            if jumlah_potong > 0:
                st.success(f"🔥 Berhasil! {jumlah_potong} item material yang sukses terinstal telah memotong stok gudang intern!")
                st.balloons()
            else:
                st.info("Tidak ada item baru yang perlu dipotong stoknya (atau status belum diubah ke 'Sudah Terinstal ✅').")

        # --- TOMBOL 2: AUTO TELEGRAM BOT ---
        st.markdown("### 🚀 2. Kirim Ringkasan Lapangan ke Grup Telegram")
        if st.button("🚀 Kirim Laporan ke Telegram", type="primary", use_container_width=True):
            if not bot_token or not chat_id:
                st.error("⚠️ Gagal mengirim! Tolong isi terlebih dahulu 'Bot Token ID' dan 'Chat ID' di Sidebar sebelah kiri!")
            else:
                # Membuat isi pesan teks otomatis
                total_data = len(st.session_state.log_scan_harian)
                terinstal = len(st.session_state.log_scan_harian[st.session_state.log_scan_harian['Status Pemasangan Sore'] == "Sudah Terinstal ✅"])
                retur = len(st.session_state.log_scan_harian[st.session_state.log_scan_harian['Status Pemasangan Sore'] == "Belum Terinstal / Retur ❌"])
                
                pesan_tele = f"📊 *LAPORAN REKAPITULASI LOGISTIK SORE*\n"
                pesan_tele += f"📅 Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                pesan_tele += f"----------------------------------------\n"
                pesan_tele += f"✅ *Total Terinstal:* {terinstal} Item\n"
                pesan_tele += f"❌ *Total Retur/Gagal:* {retur} Item\n"
                pesan_tele += f"⏳ *Belum Dilaporkan:* {total_data - terinstal - retur} Item\n\n"
                pesan_tele += f"📜 *Rincian Lapangan:*\n"
                
                for _, r in st.session_state.log_scan_harian.iterrows():
                    mat = r['Serial Number (SN)'] if r['Serial Number (SN)'] != "-" else r['Kabel Precon']
                    pesan_tele += f"• *{r['Nama Teknisi']}* | {mat[:20]}.. | {r['Status Pemasangan Sore']}\n"
                
                # Request Kirim ke Telegram API
                url_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                try:
                    res = requests.post(url_api, json={"chat_id": chat_id, "text": pesan_tele, "parse_mode": "Markdown"})
                    if res.status_code == 200: st.success("🎉 BOOM! Laporan sore berhasil ditembak langsung ke grup Telegram Anda!")
                    else: st.error(f"Gagal mengirim. Respons server: {res.text}")
                except Exception as e:
                    st.error(f"Terjadi Gangguan Jaringan: {e}")

        # --- DOWNLOAD BERKAS UPDATE ---
        st.markdown("### 📥 3. Unduh Berkas Hasil Akhir")
        csv_final_data = st.session_state.log_scan_harian.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Berkas Rekap Logistik (.CSV)", data=csv_final_data, file_name=f"REKAP_IKR_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
    else:
        st.warning("Data kosong. Silakan input atau scan material di menu Pagi terlebih dahulu.")

# ==================== MENU 3: DASHBOARD GRAFIK & ALERT STOK CRITICAL ====================
elif menu == "📊 Dashboard & Stok Gudang":
    st.subheader("📊 Dashboard Analisa & Pemantauan Stok Gudang")
    
    # 🚨 NOTIFIKASI CRITICAL STOCK ALERT BELOW 10 PCS 🚨
    critical_items = []
    
    # Check Device Stock
    if st.session_state.df_device is not None:
        df_dev = st.session_state.df_device
        num_cols = df_dev.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            qty_col = num_cols[0]
            # Ambil item yang stoknya di bawah 10
            for _, r in df_dev[df_dev[qty_col] < 10].iterrows():
                critical_items.append(f"📟 {r.iloc[0]} (Sisa: {int(r[qty_col])} Pcs)")
                
    # Check Precon Stock
    if st.session_state.df_precon is not None:
        df_prec = st.session_state.df_precon
        num_cols_p = df_prec.select_dtypes(include=['number']).columns
        if len(num_cols_p) > 0:
            qty_col_p = num_cols_p[0]
            desc_col = 'Description' if 'Description' in df_prec.columns else df_prec.columns[0]
            for _, r in df_prec[df_prec[qty_col_p] < 10].iterrows():
                critical_items.append(f"🧵 {r[desc_col]} (Sisa: {int(r[qty_col_p])} Mtr/Pcs)")

    if critical_items:
        st.error("🚨 **PERINGATAN STOK GUDANG AMBLES (DI BAWAH 10 PCS):**")
        for item in critical_items:
            st.markdown(f"- {item}")
    else:
        st.success("✅ Seluruh kondisi stok aman di atas 10 Pcs, aman terkendali, cuy!")

    # TABEL & GRAFIK INTERAKTIF
    t1, t2 = st.tabs(["📟 Stock Device", "🧵 Stock PRECON"])
    with t1:
        if st.session_state.df_device is not None:
            df_plot = st.session_state.df_device.copy()
            num_cols = df_plot.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                st.markdown("#### 📈 Grafik Visual Saldo Stok Device")
                chart_data = pd.DataFrame({
                    'Nama Barang': df_plot.iloc[:, 0].astype(str),
                    'Jumlah Stok': df_plot[num_cols[0]].fillna(0)
                }).set_index('Nama Barang')
                st.bar_chart(chart_data)
            st.dataframe(st.session_state.df_device, use_container_width=True)
        else: st.info("File Excel tidak terdeteksi.")
        
    with t2:
        if st.session_state.df_precon is not None:
            df_plot_p = st.session_state.df_precon.copy()
            num_cols_p = df_plot_p.select_dtypes(include=['number']).columns
            desc_col = 'Description' if 'Description' in df_plot_p.columns else df_plot_p.columns[0]
            if len(num_cols_p) > 0:
                st.markdown("#### 📈 Grafik Visual Saldo Stok Precon")
                chart_data_p = pd.DataFrame({
                    'Ukuran Kabel': df_plot_p[desc_col].astype(str),
                    'Jumlah Saldo': df_plot_p[num_cols_p[0]].fillna(0)
                }).set_index('Ukuran Kabel')
                st.bar_chart(chart_data_p)
            st.dataframe(st.session_state.df_precon, use_container_width=True)
        else: st.info("File Excel tidak terdeteksi.")

# ==================== MENU 4: HISTORI EXCEL TEKNISI ====================
elif menu == "👨‍🔧 Histori Sheet Teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan = st.selectbox("Pilih Nama Tim:", DAFTAR_TEKNISI)
    df_tek = load_excel_sheet(pilihan)
    if df_tek is not None: st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
    else: st.info(f"Sheet bernama '{pilihan}' tidak ditemukan di dalam file Excel.")
