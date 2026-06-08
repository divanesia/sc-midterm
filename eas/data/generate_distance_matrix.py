import pandas as pd
import numpy as np
import requests
import time
import os

# 1. Konfigurasi Path
file_input = 'eas/data/koordinat_eas.csv'
folder_output = 'eas/data/'

# Bikin folder output kalau belum ada
if not os.path.exists(folder_output):
    os.makedirs(folder_output)

# 2. Baca Data
df = pd.read_csv(file_input)

# [PENTING] Cleansing Koordinat Ekstra Kuat
def bersihkan_latitude(val):
    if pd.isna(val): return 0.0
    val_bersih = str(val).replace(',', '').replace('.', '').replace(' ', '')
    angka_saja = val_bersih.replace('-', '')
    
    if len(angka_saja) > 1:
        hasil = angka_saja[:1] + '.' + angka_saja[1:]
    else:
        hasil = angka_saja
        
    return float('-' + hasil) if '-' in str(val) else float(hasil)

def bersihkan_longitude(val):
    if pd.isna(val): return 0.0
    val_bersih = str(val).replace(',', '').replace('.', '').replace(' ', '')
    
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

print("⚙️ MEMPROSES MATRIKS JARAK RIIL (OSRM API)...")
print("="*50)

# [Fitur Tambahan] Override Jarak Manual (dalam Kilometer)
# Ubah nilainya jika ada node spesifik yang butuh penyesuaian jarak manual agar rute optimalnya akurat
override_jarak = {
    ("BE", "DC"): 5.5, # Silakan ganti 5.5 dengan jarak riil yang seharusnya
    ("DC", "BE"): 5.5
}

# 4. Looping pembuatan matriks per klaster
for klaster in klaster_list:
    df_klaster = df_puskesmas[df_puskesmas['Wilayah'].str.contains(klaster, case=False, na=False)].copy()
    
    # Gabungkan Depot (Indeks 0) dengan Puskesmas
    df_gabungan = pd.concat([pd.DataFrame([depot_row]), df_klaster]).reset_index(drop=True)
    
    jumlah_titik = len(df_gabungan)
    nama_lokasi = df_gabungan['Nama Puskesmas'].tolist()
    
    # Inisialisasi Matriks kosong
    matriks_jarak = np.zeros((jumlah_titik, jumlah_titik))
    
    # 5. Hitung jarak riil jalan raya pakai OSRM
    for i in range(jumlah_titik):
        for j in range(jumlah_titik):
            if i == j:
                matriks_jarak[i][j] = 0.0
            else:
                nama_asal = df_gabungan.loc[i, 'Nama Puskesmas']
                nama_tujuan = df_gabungan.loc[j, 'Nama Puskesmas']

                # Cek apakah rute ini ada di daftar override manual
                if (nama_asal, nama_tujuan) in override_jarak:
                    matriks_jarak[i][j] = override_jarak[(nama_asal, nama_tujuan)]
                    continue

                lon_asal = df_gabungan.loc[i, 'Longitude']
                lat_asal = df_gabungan.loc[i, 'Latitude']
                lon_tujuan = df_gabungan.loc[j, 'Longitude']
                lat_tujuan = df_gabungan.loc[j, 'Latitude']
                
                # Request ke API OSRM
                url = f"http://router.project-osrm.org/route/v1/driving/{lon_asal},{lat_asal};{lon_tujuan},{lat_tujuan}?overview=false"
                
                try:
                    response = requests.get(url).json()
                    if response.get('code') == 'Ok':
                        # OSRM mengembalikan jarak dalam METER, kita bagi 1000 jadi KILOMETER
                        jarak_meter = response['routes'][0]['distance']
                        jarak_km = jarak_meter / 1000
                        matriks_jarak[i][j] = round(jarak_km, 3)
                    else:
                        print(f"⚠️ Gagal mencari rute {nama_asal} ke {nama_tujuan}")
                        matriks_jarak[i][j] = 999.0
                except Exception as e:
                    print(f"❌ Error API dari {nama_asal} ke {nama_tujuan}: {e}")
                    matriks_jarak[i][j] = 999.0
                
                # Kasih jeda sedikit biar server OSRM tidak nge-block IP kalian
                time.sleep(0.2) 
                
    # 6. Simpan ke dalam DataFrame dan Export ke CSV
    df_matriks_jarak = pd.DataFrame(matriks_jarak, index=nama_lokasi, columns=nama_lokasi)
    file_jarak = f"{folder_output}matriks_jarak_riil_{klaster.lower()}.csv"
    
    df_matriks_jarak.to_csv(file_jarak)
    
    print(f"✅ Klaster {klaster.upper()}: {jumlah_titik} titik (1 Depot + {jumlah_titik-1} Puskesmas) selesai!")
    
print("="*50)
print("🎉 SEMUA MATRIKS JARAK RIIL BERHASIL DIBUAT!")