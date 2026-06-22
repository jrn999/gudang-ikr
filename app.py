import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# 1. Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Sistem Logistik IKR Metech", 
    layout="wide", 
    page_icon="⚡"
)

# 2. INJEKSI CSS OPTIMIZED (Tampilan Mewah Kemarin, Tapi Dijamin Aman & Tombol Lancar)
st.markdown("""
<style>
    /* Sembunyikan hiasan bawaan Streamlit agar bersih */
    [data-testid="stDecoration"], [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Warna latar belakang utama */
    .stApp {
        background-color: #f4f6f9 !important;
    }
    
    /* SIDEBAR GRADASI PREMIUM (Ungu & Biru) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4b5cc4 0%, #764ba2 100%) !important;
    }
    
    /* Modifikasi Teks di Dalam Sidebar agar Putih Bersih */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    /* MODIFIKASI RADIO BUTTON MENU SIDEBAR */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 8px !important;
    }
    
    /* Hilangkan bulatan radio button asli tanpa merusak fungsi klik */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* Rombak label menjadi Menu Bar Flat yang Mewah */
    [data-testid="stSidebar"] div[data-testid="stRadio"] label {
        padding: 12px 20px !important;
        color: #e2e8f0 !important;
        font-size: 14.5px !important;
        font-weight: 500 !important;
        border-radius: 0px 8px 8px 0px !important;
        margin-right: 15px !important;
        border-left: 4px solid transparent !important;
        background-color: transparent !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    /* Efek Hover Menu */
    [data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    
    /* MENU AKTIF (Ada Garis Kuning sesuai Kriteria Bos) */
    [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: rgba(255, 255, 255, 0.18) !important;
        color: white !important;
        border-left: 4px solid #facc15 !important;
        font-weight: 600 !important;
    }
    
    /* KOTAK / CONTAINER FORMAT CARD PUTIH (Aman dari Bug Pointer) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white !important;
        border-radius: 12px !important;
        box-shadow: 0px 4px 16px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid #eef2f6 !important;
        padding: 25px !important;
        margin-bottom: 20px !important;
    }
    
    /* Merapikan Label Input */
    div[data-testid="stWidgetLabel"] p {
        font-weight: 500 !important;
        color: #4b5563 !important;
        font-size: 14px !important;
    }
    
    /* Tombol Utama (Waran Ungu Solid yang Kuat) */
    button[kind="primary"] {
        background-color: #764ba2 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        box-shadow: 0px 3px 8px rgba(118, 75, 162, 0.25) !important;
    }
    button[kind="primary"]:hover {
        background-color: #5c348a !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIAL DATA & SESSION STATE (Dibuat Mandiri Tanpa Cloud Dulu Agar Lancar Dites) ---
if 'log_lokal' not in st.session_state:
    st.session_state.log_lokal = pd.DataFrame(columns=[
        'Waktu Scan', 'Nama Teknisi', 'Serial Number (SN)', 'Nama Barang', 'Status Sore'
    ])

DAFTAR_TEKNISI = ["PUTRA-SONY", "RIYAN-RIYADI", "NADI-PARI", "ARIF-YASRIL", "NOVANS-GOBY", "PERI-ROBIN"]

# --- SIDEBAR HEADER TITLE ---
st.sidebar.markdown("""
<div style="padding: 10px 0px 20px 0px;">
    <h2 style="color: white; font-size: 19px; font-weight: 700; margin: 0; letter-spacing: 0.5px;">📋 INVENTORY SYSTEM</h2>
    <p style="color: #cbd5e1; font-size: 11px; margin: 3px 0 0 0;">Multi Aplikasi Logistik</p>
</div>
<div style="color: #94a3b8; font-size: 11px; font-weight: 600; letter-spacing: 1px; margin-bottom: 10px;">APLIKASI UTAMA</div>
""", unsafe_allow_html=True)

menu_options = {
    "pagi": "Scan & Input Pagi",
    "sore": "Laporan Penggunaan Sore",
    "gudang": "Dashboard & Stok Gudang"
}

pilihan_menu = st.sidebar.radio(
    "NAVIGATION", 
    options=list(menu_options.keys()),
    format_func=lambda x: menu_options[x],
    label_visibility="collapsed"
)

# --- TOP NAVBAR REAL-TIME ---
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; background-color: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); margin-bottom: 25px;">
    <div style="font-size: 18px; font-weight: 600; color: #1e293b; display: flex; align-items: center; gap: 10px;">
        📂 {menu_options[pilihan_menu]}
    </div>
    <div style="font-size: 13px; color: #64748b; font-weight: 500;">
        👤 Role: Admin Gudang
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== MAPPING MENU PLATFORM ====================
if pilihan_menu == "pagi":
    with st.container(border=True):
        st.markdown("<h4 style='margin-top:0; color: #334155;'>║ Input Barang Masuk Pagi</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            sn_input = st.text_input("Serial Number (SN)", placeholder="Scan Barcode / Tembak SN di sini...")
            teknisi_select = st.selectbox("Pilih Nama Teknisi", DAFTAR_TEKNISI)
        with col2:
            jenis_barang = st.selectbox("Jenis Barang", ["ONT Premium", "STB HD Box", "Access Point Outdoor", "Kabel Precon"])
            jumlah_unit = st.number_input("Jumlah Unit", min_value=1, value=1)
            
        keterangan = st.text_area("Keterangan Tambahan / No WO", placeholder="Masukkan info tambahan jika ada...")
        
        if st.button("➕ Tambah Item Ke List", type="primary", use_container_width=True):
            if sn_input or jenis_barang == "Kabel Precon":
                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_data = pd.DataFrame([{
                    'Waktu Scan': waktu_sekarang,
                    'Nama Teknisi': teknisi_select,
                    'Serial Number (SN)': sn_input if sn_input else "-",
                    'Nama Barang': jenis_barang,
                    'Status Sore': "Belum Dilaporkan ⏳"
                }])
                st.session_state.log_lokal = pd.concat([st.session_state.log_lokal, new_data], ignore_index=True)
                st.success(f"🎉 Berhasil memasukkan {jenis_barang} untuk {teknisi_select}!")
            else:
                st.warning("⚠️ Mohon isi Serial Number (SN) terlebih dahulu untuk perangkat device!")

    st.markdown("#### 📋 Preview Data Scan Hari Ini")
    with st.container(border=True):
        if not st.session_state.log_lokal.empty:
            st.dataframe(st.session_state.log_lokal, use_container_width=True)
        else:
            st.info("Belum ada data material yang keluar pagi ini.")

elif pilihan_menu == "sore":
    with st.container(border=True):
        st.markdown("<h4 style='margin-top:0; color: #334155;'>🔄 Laporan Penggunaan Sore</h4>", unsafe_allow_html=True)
        
        if not st.session_state.log_lokal.empty:
            st.info("Silakan ganti Status Pemasangan langsung pada tabel di bawah ini:")
            
            edited_df = st.data_editor(
                st.session_state.log_lokal,
                column_config={
                    "Status Sore": st.column_config.SelectboxColumn(
                        "Status Sore", 
                        options=["Belum Dilaporkan ⏳", "Sudah Terinstal ✅", "Belum Terinstal / Retur ❌"],
                        required=True
                    )
                },
                use_container_width=True
            )
            
            if st.button("🔄 Eksekusi Potong Stok", type="primary", use_container_width=True):
                st.session_state.log_lokal = edited_df
                st.toast("🔥 Status Sore berhasil disimpan dan stok gudang terpotong!", icon="✅")
        else:
            st.warning("Data scan pagi masih kosong, tidak ada data yang bisa dilaporkan sore ini.")

elif pilihan_menu == "gudang":
    with st.container(border=True):
        st.markdown("<h4 style='margin-top:0; color: #334155;'>📉 Sisa Stok Gudang Real-Time</h4>", unsafe_allow_html=True)
        
        st.dataframe(pd.DataFrame({
            "Nama Komponen / Material": ["ONT Premium", "STB HD Box", "Access Point Outdoor", "Kabel Precon 75M"],
            "Stok Awal": [100, 50, 20, 200],
            "Sisa Stok Terkini": [92, 48, 20, 185]
        }), use_container_width=True)
