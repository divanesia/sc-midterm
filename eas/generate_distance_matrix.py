import pandas as pd
import numpy as np
from geopy.distance import geodesic
import os

# 1. Konfigurasi Path
# Menggunakan path relatif karena kamu nge-run dari folder sc/midterm/
file_input = 'C:/diva/1TS/6/sc/midterm/eas/data/koordinat_eas.csv'
folder_output = 'C:/diva/1TS/6/sc/midterm/eas/data/'

# Bikin folder output kalau belum ada
if not os.path.exists(folder_output):
    os.makedirs(folder_output)

# 2. Baca Data
df = pd.read_csv(file_input)

# [PENTING] Cleansing Koordinat Ekstra Kuat
def bersihkan_latitude(val):
    if pd.isna(val): return 0.0
    # Hapus semua koma, titik, dan spasi
    val_bersih = str(val).replace(',', '').replace('.', '').replace(' ', '')
    # Ambil angkanya saja (buang minus sementara)
    angka_saja = val_bersih.replace('-', '')
    
    # Pasang titik setelah angka pertama (menjadi -7.xxxxx)
    if len(angka_saja) > 1:
        hasil = angka_saja[:1] + '.' + angka_saja[1:]
    else:
        hasil = angka_saja
        
    return float('-' + hasil) if '-' in str(val) else float(hasil)

def bersihkan_longitude(val):
    if pd.isna(val): return 0.0
    # Hapus semua koma, titik, dan spasi
    val_bersih = str(val).replace(',', '').replace('.', '').replace(' ', '')
    
    # Pasang titik setelah 3 angka pertama (menjadi 112.xxxxx)
    if len(val_bersih) > 3:
        hasil = val_bersih[:3] + '.' + val_bersih[3:]
    else:
        hasil = val_bersih
        
    return float(hasil)

# Terapkan fungsi pembersih yang baru
df['Latitude'] = df['Latitude'].apply(bersihkan_latitude)
df['Longitude'] = df['Longitude'].apply(bersihkan_longitude)

# 3. Pisahkan UPTD (Depot) dan Puskesmas
depot_row = df[df['Nama Puskesmas'].str.contains('UPTD', case=False, na=False)].iloc[0]
df_puskesmas = df[~df['Nama Puskesmas'].str.contains('UPTD', case=False, na=False)]

# Daftar wilayah klaster
klaster_list = ['Barat', 'Pusat', 'Selatan', 'Timur', 'Utara']

print("⚙️ MEMPROSES MATRIKS JARAK...")
print("="*50)

# 4. Looping pembuatan matriks per klaster
for klaster in klaster_list:
    df_klaster = df_puskesmas[df_puskesmas['Wilayah'].str.contains(klaster, case=False, na=False)].copy()
    
    # Gabungkan Depot (Indeks 0) dengan Puskesmas
    df_gabungan = pd.concat([pd.DataFrame([depot_row]), df_klaster]).reset_index(drop=True)
    
    jumlah_titik = len(df_gabungan)
    nama_lokasi = df_gabungan['Nama Puskesmas'].tolist()
    
    # Inisialisasi Matriks kosong
    matriks_jarak = np.zeros((jumlah_titik, jumlah_titik))
    
    # 5. Hitung jarak antar semua pasang titik
    for i in range(jumlah_titik):
        for j in range(jumlah_titik):
            if i == j:
                matriks_jarak[i][j] = 0.0
            else:
                koordinat_asal = (df_gabungan.loc[i, 'Latitude'], df_gabungan.loc[i, 'Longitude'])
                koordinat_tujuan = (df_gabungan.loc[j, 'Latitude'], df_gabungan.loc[j, 'Longitude'])
                
                # Hitung Jarak (Kilometer)
                jarak_km = geodesic(koordinat_asal, koordinat_tujuan).kilometers
                matriks_jarak[i][j] = round(jarak_km, 3)
                
    # 6. Simpan ke dalam DataFrame dan Export ke CSV
    df_matriks_jarak = pd.DataFrame(matriks_jarak, index=nama_lokasi, columns=nama_lokasi)
    file_jarak = f"{folder_output}matriks_jarak_{klaster.lower()}.csv"
    
    df_matriks_jarak.to_csv(file_jarak)
    
    print(f"✅ Klaster {klaster.upper()}: {jumlah_titik} titik (1 Depot + {jumlah_titik-1} Puskesmas)")
    
print("="*50)
print("🎉 SEMUA MATRIKS JARAK BERHASIL DIBUAT!")