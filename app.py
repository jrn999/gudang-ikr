import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Sistem Logistik IKR Pro", layout="wide", page_icon="⚡")

# 1. DATABASE INITIALIZATION (Disamakan dengan Nama Kolom Excel Asli Kamu)
FILE_MASTER_SN = "db_master_sn.csv"
FILE_TRANSAKSI = "db_transaksi_material.csv"
FILE_STOK_PRECON = "db_stok_precon.csv"

def init_databases():
    # Master SN Awal
    if not os.path.exists(FILE_MASTER_SN):
        df_m = pd.DataFrame({
            'SN': ['ZTEGDD2B1636', 'ZTEGDD2B1539', '48575443AB7FD0B2', '48575443DAF26BB1'],
            'Nama_Barang': ['ont zte', 'ont zte', 'ont huawey', 'ont huawey'],
            'Kode_Gudang': ['DN/TRF-EMR/26/02132', 'DN/TRF-EMR/26/02132', 'DN/TRF-EMR/26/03280', 'DN/TRF-EMR/26/03280'],
            'Deskripsi': ['ZTE-ONT ZXHN-F672Y (DUAL BAND)', 'ZTE-ONT ZXHN-F672Y (DUAL BAND)', 'HUAWEI-ONT HG8145V6 (DUAL BAND)/D', 'HUAWEI-ONT HG8145V6 (DUAL BAND)/D']
        })
        df_m.to_csv(FILE_MASTER_SN, index=False)

    # Stok Real Kabel Precon Gudang (WH METECH)
    if not os.path.exists(FILE_STOK_PRECON):
        df_p = pd.DataFrame({
            'Ukuran': ['75MTR', '125MTR', '175MTR', '225MTR', '300MTR'],
            'Stok_Gudang': [24, 15, 24, 4, 29], 
            'UOM': ['ROL', 'ROL', 'ROL', 'ROL', 'ROL']
        })
        df_p.to_csv(FILE_STOK_PRECON, index=False)

    # Log Transaksi Keluar (Struktur Kolom Sesuai Sheet 2. TRANSAKSI KELUAR)
    if not os.path.exists(FILE_TRANSAKSI):
        df_t = pd.DataFrame(columns=[
            'SN', 'Nama_Barang', 'Kode_Gudang', 'Tanggal_Keluar', 'Teknisi', 'Status_Instal', 'Catatan_Telegram'
        ])
        df_t.to_csv(FILE_TRANSAKSI, index=False)

init_databases()

# Load Data Terkini
df_master = pd.read_csv(FILE_MASTER_SN)
df_transaksi = pd.read_csv(FILE_TRANSAKSI)
df_precon = pd.read_csv(FILE_STOK_PRECON)

# DAFTAR TIM TEKNISI ASLI
LIST_TEKNISI = [
    "PUTRA-SONY", "NADI-PARI", "RIYAN-RIYADI", "ARIF-YASRIL", 
    "NOVAN-GOBY", "PERI-ROBIN", "TEDI-DODI", "REFKY-DODI", 
    "RAHMAN-AGUS", "IDDO-NAUFAL"
]

# --- SIDEBAR NAVIGASI ---
st.sidebar.image("https://img.icons8.com/fluent/96/000000/cable-release.png", width=70)
st.sidebar.title("IKR Logistics Pro")
st.sidebar.markdown(f"**Role:** Warehouse Admin\n**Status:** Online 🟢")
st.sidebar.markdown("---")
menu = st.sidebar.radio("MENU UTAMA:", [
    "📊 Dashboard Eksekutif Bos", 
    "📥 Input Transaksi Keluar", 
    "🔍 Lacak Material & SN", 
    "📦 Manajemen Stok Gudang"
])

# ==================== MENU 1: DASHBOARD EXECUTIVE ====================
if menu == "📊 Dashboard Eksekutif Bos":
    st.title("📊 Performa Logistik & Distribusi Material IKR")
    st.markdown("---")
    
    # Hitung Metrik
    total_device = len(df_transaksi[df_transaksi['Nama_Barang'].str.contains('ont|stb', case=False, na=False)])
    sudah_pasang = len(df_transaksi[df_transaksi['Status_Instal'] == 'SUDAH INSTAL'])
    belum_pasang = len(df_transaksi[df_transaksi['Status_Instal'] == 'BELUM INSTAL'])
    rasio_selesai = (sudah_pasang / total_device * 100) if total_device > 0 else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL DEVICE KELUAR", f"{total_device} Unit")
    m2.metric("🟢 SELESAI TERPASANG", f"{sudah_pasang} Unit")
    m3.metric("🔴 BELUM INSTAL", f"{belum_pasang} Unit")
    m4.metric("📈 PERSENTASE WO", f"{rasio_selesai:.1f}%")
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("⚡ Status WO Pasang Baru per Tim Teknisi")
        if len(df_transaksi) > 0:
            df_perf = df_transaksi[df_transaksi['Status_Instal'].isin(['SUDAH INSTAL', 'BELUM INSTAL'])]
            if len(df_perf) > 0:
                fig = px.bar(df_perf, x='Teknisi', color='Status_Instal', barmode='group',
                             color_discrete_map={'SUDAH INSTAL': '#2ECC71', 'BELUM INSTAL': '#E74C3C'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada data pemasangan device harian.")
        else:
            st.info("Data transaksi harian kosong.")
            
    with col_right:
        st.subheader("🧵 Sisa Stok Kabel Precon Gudang Utama (Rol)")
        fig_precon = px.bar(df_precon, x='Ukuran', y='Stok_Gudang', text='Stok_Gudang',
                            color='Ukuran', color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_precon, use_container_width=True)

    st.subheader("📋 Log Transaksi Terkini (Siap Copy ke Excel)")
    st.dataframe(df_transaksi.tail(15), use_container_width=True)

# ==================== MENU 2: INPUT TRANSAKSI KELUAR ====================
elif menu == "📥 Input Transaksi Keluar":
    st.title("📥 Input Pengeluaran Harian Material IKR")
    st.markdown("---")
    
    kategori_input = st.radio("PILIH KATEGORI BARANG:", ["Device (ONT / STB)", "Kabel Precon Dropcore"], horizontal=True)
    
    if kategori_input == "Device (ONT / STB)":
        with st.form("form_device", clear_on_submit=True):
            scan_sn = st.text_input("👉 SCAN BARCODE / KETIK SN DEVICE DI SINI:").strip().upper()
            pilih_tek = st.selectbox("Serahkan ke Tim Teknisi:", LIST_TEKNISI)
            status_wo = st.selectbox("Status Instalasi Lapangan:", ["BELUM INSTAL", "SUDAH INSTAL"])
            catatan = st.text_input("Catatan / No Tiket Telegram:")
            submit_dev = st.form_submit_button("💾 Validasi & Simpan Transaksi")
            
        if submit_dev and scan_sn:
            # VALIDASI: Proteksi SN Duplikat
            if scan_sn in df_transaksi['SN'].values:
                st.error(f"❌ ERROR: SN `{scan_sn}` Gagal Dikeluarkan! Perangkat ini sudah pernah keluar gudang sebelumnya (Double Scan Berbahaya)!")
            else:
                # Ambil info data barang dari master
                match_master = df_master[df_master['SN'] == scan_sn]
                if len(match_master) > 0:
                    nama_brg = match_master.iloc[0]['Nama_Barang']
                    kode_gdg = match_master.iloc[0]['Kode_Gudang']
                else:
                    nama_brg = "ont zte"  # default jika tidak ada di master data
                    kode_gdg = "DN/TRF-EMR/26/"
                
                new_trx = {
                    'SN': scan_sn,
                    'Nama_Barang': nama_brg,
                    'Kode_Gudang': kode_gdg,
                    'Tanggal_Keluar': datetime.now().strftime('%Y-%m-%d'),
                    'Teknisi': pilih_tek,
                    'Status_Instal': status_wo,
                    'Catatan_Telegram': catatan
                }
                df_transaksi = pd.concat([df_transaksi, pd.DataFrame([new_trx])], ignore_index=True)
                df_transaksi.to_csv(FILE_TRANSAKSI, index=False)
                st.success(f"✅ BERHASIL! Perangkat SN `{scan_sn}` berhasil dialokasikan ke tim {pilih_tek}.")
                st.balloons()

    elif kategori_input == "Kabel Precon Dropcore":
        with st.form("form_precon", clear_on_submit=True):
            pilih_ukuran = st.selectbox("Pilih Ukuran Panjang Kabel Precon:", df_precon['Ukuran'].tolist())
            pilih_tek_kabel = st.selectbox("Serahkan ke Tim Teknisi:", LIST_TEKNISI)
            qty_kabel = st.number_input("Jumlah Pengeluaran (Rol):", min_value=1, max_value=20, value=1)
            catatan_k = st.text_input("Keterangan Lokasi Pasang / No Tiket:")
            submit_kabel = st.form_submit_button("💾 Potong Stok & Simpan Kabel")
            
        if submit_kabel:
            # VALIDASI: Stok mencukupi atau tidak
            stok_sekarang = df_precon.loc[df_precon['Ukuran'] == pilih_ukuran, 'Stok_Gudang'].values[0]
            
            if stok_sekarang < qty_kabel:
                st.error(f"❌ GAGAL! Stok Gudang untuk Kabel {pilih_ukuran} tidak cukup. Sisa stok: {stok_sekarang} Rol, Anda meminta: {qty_kabel} Rol.")
            else:
                # 1. Potong stok tabel precon
                df_precon.loc[df_precon['Ukuran'] == pilih_ukuran, 'Stok_Gudang'] -= qty_kabel
                df_precon.to_csv(FILE_STOK_PRECON, index=False)
                
                # 2. Catat ke log transaksi harian
                new_trx_k = {
                    'SN': pilih_ukuran,  # Menyimpan ukuran kabel di kolom SN agar fleksibel
                    'Nama_Barang': 'Kabel Precon',
                    'Kode_Gudang': 'WH-METECH',
                    'Tanggal_Keluar': datetime.now().strftime('%Y-%m-%d'),
                    'Teknisi': pilih_tek_kabel,
                    'Status_Instal': 'TERPAKAI',
                    'Catatan_Telegram': f"{qty_kabel} Rol - {catatan_k}"
                }
                df_transaksi = pd.concat([df_transaksi, pd.DataFrame([new_trx_k])], ignore_index=True)
                df_transaksi.to_csv(FILE_TRANSAKSI, index=False)
                st.success(f"🎉 SUKSES POTONG STOK! {qty_kabel} Rol Kabel {pilih_ukuran} keluar ke {pilih_tek_kabel}. Sisa stok gudang: {stok_sekarang - qty_kabel} Rol.")

# ==================== MENU 3: TRACKING & LACAK MATERIAL ====================
elif menu == "🔍 Lacak Material & SN":
    st.title("🔍 Pusat Pelacakan Serial Number & Riwayat Tim")
    st.markdown("---")
    
    opsi_cari = st.radio("Metode Pelacakan:", ["Berdasarkan Nomor SN Perangkat", "Berdasarkan Riwayat Teknisi"], horizontal=True)
    
    if opsi_cari == "Berdasarkan Nomor SN Perangkat":
        cari_sn = st.text_input("Masukkan / Scan Nomor SN:").strip().upper()
        if cari_sn:
            hasil = df_transaksi[df_transaksi['SN'] == cari_sn]
            if len(hasil) > 0:
                st.success("🎯 Data Histori Pengeluaran SN Ditemukan!")
                st.dataframe(hasil, use_container_width=True)
            else:
                st.warning("⚠️ Nomor SN ini belum pernah tercatat keluar gudang.")
                
    elif opsi_cari == "Berdasarkan Riwayat Teknisi":
        pilih_tek_cari = st.selectbox("Pilih Nama Tim Teknisi:", LIST_TEKNISI)
        hasil_tek = df_transaksi[df_transaksi['Teknisi'] == pilih_tek_cari]
        if len(hasil_tek) > 0:
            st.info(f"📋 Tim {pilih_tek_cari} membawa {len(hasil_tek)} material dari gudang:")
            st.dataframe(hasil_tek, use_container_width=True)
        else:
            st.warning(f"Tim {pilih_tek_cari} belum mengambil barang minggu ini.")

# ==================== MENU 4: MANAGEMENT STOK GUDANG ====================
elif menu == "📦 Manajemen Stok Gudang":
    st.title("📦 Kontrol & Restock Fisik Gudang")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🧵 Tambah Stok Masuk Kabel Precon", "➕ Registrasi SN Baru"])
    
    with tab1:
        st.subheader("Data Stok Kabel Saat Ini")
        st.dataframe(df_precon, use_container_width=True)
        
        with st.form("tambah_stok_kabel"):
            pilih_uk_tambah = st.selectbox("Ukuran Kabel Masuk:", df_precon['Ukuran'].tolist())
            jumlah_masuk = st.number_input("Jumlah Masuk (Rol):", min_value=1, value=10)
            btn_stok_k = st.form_submit_button("📥 Tambahkan ke Gudang")
            
        if btn_stok_k:
            df_precon.loc[df_precon['Ukuran'] == pilih_uk_tambah, 'Stok_Gudang'] += jumlah_masuk
            df_precon.to_csv(FILE_STOK_PRECON, index=False)
            st.success(f"Stok Kabel {pilih_uk_tambah} berhasil ditambahkan sebanyak {jumlah_masuk} Rol!")
            st.remaining = st.rerun()
            
    with tab2:
        st.subheader("Daftarkan SN Baru dari Supplier ke Database Master")
        with st.form("regis_sn_baru"):
            n_sn = st.text_input("Input SN Baru:").strip().upper()
            n_jenis = st.selectbox("Jenis Alat:", ["ont zte", "ont huawey", "stb zte", "stb fiberhome"])
            n_kode = st.text_input("Kode Gudang / No DN:", "DN/TRF-EMR/26/")
            n_desc = st.text_input("Deskripsi Detail Perangkat:", "ZTE-ONT ZXHN-F672Y (DUAL BAND)")
            btn_regis = st.form_submit_button("💾 Daftarkan ke Database Master")
            
        if btn_regis and n_sn:
            if n_sn in df_master['SN'].values:
                st.error("Gagal! SN ini sudah terdaftar di database master.")
            else:
                new_m = {'SN': n_sn, 'Nama_Barang': n_jenis, 'Kode_Gudang': n_kode, 'Deskripsi': n_desc}
                df_master = pd.concat([df_master, pd.DataFrame([new_m])], ignore_index=True)
                df_master.to_csv(FILE_MASTER_SN, index=False)
                st.success(f"SN `{n_sn}` Berhasil Didaftarkan!")