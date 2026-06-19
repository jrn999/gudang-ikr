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

# --- MENYIMPAN DATABASE STOK DI SESSION STATE ---
if 'df_device' not in st.session_state:
    st.session_state.df_device = load_excel_sheet("Stock Device")
if 'df_precon' not in st.session_state:
    st.session_state.df_precon = load_excel_sheet("Stock PRECON")

df_master = load_master_sn()

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
    st.write("Masukkan kredensial Bot Telegram Grup Anda di sini:")
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
        if st.button("🗑️ Kosongkan Tabel Pagi (Reset)"):
            st.session_state.log_scan_harian = pd.DataFrame(columns=['Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Kabel Precon', 'No WO / Keterangan', 'Status Pemasangan Sore', 'Keterangan Tambahan Sore', 'Stok Dipotong'])
            st.session_state.status_scan_terakhir = "kosong"
            st.rerun()
    else:
        st.info("Belum ada data barang keluar pagi ini.")

# ==================== MENU 2: LAPORAN SORE ====================
elif menu == "📝 Laporan Penggunaan Sore (Update Status)":
    st.subheader("📝 Laporan Hasil Kerja Lapangan Sore Hari")
    
    if not st.session_state.log_scan_harian.empty:
        # DI SINI FIX UTAMANYA: Menggunakan SelectboxColumn, bukan SelectColumn!
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
            jumlah_potong = 0
            for idx, row in st.session_state.log_scan_harian.iterrows():
                if row['Status Pemasangan Sore'] == "Sudah Terinstal ✅" and row['Stok Dipotong'] == "Belum":
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
                    elif row['Kabel Precon'] != "-":
                        if st.session_state.df_precon is not None:
                            kolom_desk_p = st.session_state.df_precon.columns[0]
                            for c in st.session_state.df_precon.columns:
                                if 'DESC' in str(c).upper(): kolom_desk_p = c; break
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
                st.success(f"🔥 Berhasil memotong {jumlah_potong} item material dari stok gudang!")
                st.balloons()
            else:
                st.info("Tidak ada item baru yang perlu dipotong.")

        # --- TELEGRAM BOT ---
        st.markdown("### 🚀 2. Kirim Ringkasan Lapangan ke Grup Telegram")
        if st.button("🚀 Kirim Laporan ke Telegram", type="primary", use_container_width=True):
            if not bot_token or not chat_id:
                st.error("⚠️ Token ID / Chat ID di Sidebar kosong!")
            else:
                terinstal = len(st.session_state.log_scan_harian[st.session_state.log_scan_harian['Status Pemasangan Sore'] == "Sudah Terinstal ✅"])
                retur = len(st.session_state.log_scan_harian[st.session_state.log_scan_harian['Status Pemasangan Sore'] == "Belum Terinstal / Retur ❌"])
                pesan_tele = f"📊 *LAPORAN REKAP REKAP SORE METECH*\n✅ Terinstal: {terinstal} | ❌ Retur: {retur}"
                try:
                    res = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": pesan_tele})
                    if res.status_code == 200: st.success("🎉 Berhasil dikirim ke Telegram!")
                    else: st.error(f"Gagal: {res.text}")
                except Exception as e: st.error(f"Error Jaringan: {e}")

        st.markdown("### 📥 3. Unduh Berkas Hasil Akhir")
        st.download_button(label="📥 Download Berkas Rekap Logistik (.CSV)", data=st.session_state.log_scan_harian.to_csv(index=False).encode('utf-8'), file_name=f"REKAP_IKR_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
    else:
        st.warning("Data kosong. Silakan input data pagi dulu.")

# ==================== MENU 3: DASHBOARD & CEK KONEKSI EXCEL ====================
elif menu == "📊 Dashboard & Stok Gudang":
    st.subheader("📊 Dashboard Utama Gudang")
    
    st.markdown("### 📌 Status Sinkronisasi File Excel di GitHub")
    # Fix Tampilan dari image_663968.png agar mendeteksi file asli dengan benar tanpa error CSV siluman
    if os.path.exists(MASTER_SN_FILE):
        st.success(f"✅ Master SN: Terkoneksi ({MASTER_SN_FILE})")
    else:
        st.error(f"❌ Master SN: File '{MASTER_SN_FILE}' TIDAK DITEMUKAN di GitHub!")
        
    if os.path.exists(EXCEL_FILE):
        st.success(f"✅ Master Excel Stok: Terkoneksi ({EXCEL_FILE})")
    else:
        st.error(f"❌ Master Excel Stok: File '{EXCEL_FILE}' TIDAK DITEMUKAN di GitHub!")

    st.markdown("---")
    critical_items = []
    if st.session_state.df_device is not None:
        df_dev = st.session_state.df_device
        num_cols = df_dev.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            for _, r in df_dev[df_dev[num_cols[0]] < 10].iterrows():
                critical_items.append(f"📟 {r.iloc[0]} (Sisa: {int(r[num_cols[0]])} Pcs)")
                
    if st.session_state.df_precon is not None:
        df_prec = st.session_state.df_precon
        num_cols_p = df_prec.select_dtypes(include=['number']).columns
        desc_col = df_prec.columns[0]
        for c in df_prec.columns:
            if 'DESC' in str(c).upper(): desc_col = c; break
        if len(num_cols_p) > 0:
            for _, r in df_prec[df_prec[num_cols_p[0]] < 10].iterrows():
                critical_items.append(f"🧵 {r[desc_col]} (Sisa: {int(r[num_cols_p[0]])} Pcs)")

    if critical_items:
        st.error("🚨 **PERINGATAN STOK GUDANG DI BAWAH 10 PCS:**")
        for item in critical_items: st.markdown(f"- {item}")
    else:
        st.success("✅ Seluruh kondisi stok material aman terkendali, cuy!")

    t1, t2 = st.tabs(["📟 Stock Device", "🧵 Stock PRECON"])
    with t1:
        if st.session_state.df_device is not None:
            df_plot = st.session_state.df_device.copy()
            num_cols = df_plot.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                st.bar_chart(pd.DataFrame({'Jumlah Stok': df_plot[num_cols[0]].fillna(0)}).set_index(df_plot.iloc[:, 0].astype(str)))
            st.dataframe(st.session_state.df_device, use_container_width=True)
    with t2:
        if st.session_state.df_precon is not None:
            df_plot_p = st.session_state.df_precon.copy()
            num_cols_p = df_plot_p.select_dtypes(include=['number']).columns
            desc_col = df_plot_p.columns[0]
            for c in df_plot_p.columns:
                if 'DESC' in str(c).upper(): desc_col = c; break
            if len(num_cols_p) > 0:
                st.bar_chart(pd.DataFrame({'Jumlah Saldo': df_plot_p[num_cols_p[0]].fillna(0)}).set_index(df_plot_p[desc_col].astype(str)))
            st.dataframe(st.session_state.df_precon, use_container_width=True)

# ==================== MENU 4: HISTORI EXCEL TEKNISI ====================
elif menu == "👨‍🔧 Histori Sheet Teknisi":
    st.subheader("👨‍🔧 Histori Sheet Penggunaan Teknisi")
    pilihan = st.selectbox("Pilih Nama Tim:", DAFTAR_TEKNISI)
    df_tek = load_excel_sheet(pilihan)
    if df_tek is not None: st.dataframe(df_tek.dropna(how='all'), use_container_width=True)
    else: st.info(f"Sheet bernama '{pilihan}' tidak ditemukan di dalam file Excel.")
