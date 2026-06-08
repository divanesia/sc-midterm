import pandas as pd
import numpy as np
import requests
import time
import os

# 1. Konfigurasi Path
file_input = 'eas\data\koordinat_eas.csv'
folder_output = 'eas\data'

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

df['Latitude'] = df['Latitude'].apply(bersihkan_latitude)
df['Longitude'] = df['Longitude'].apply(bersihkan_longitude)

# 3. Pisahkan UPTD (Depot) dan Puskesmas
depot_row = df[df['Nama Puskesmas'].str.contains('UPTD', case=False, na=False)].iloc[0]
df_puskesmas = df[~df['Nama Puskesmas'].str.contains('UPTD', case=False, na=False)]

klaster_list = ['Barat', 'Pusat', 'Selatan', 'Timur', 'Utara']

print("⚙️ MEMPROSES MATRIKS WAKTU (OSRM API)...")
print("="*50)

# [Fitur Tambahan] Override Waktu Manual (dalam menit)
# Silakan ubah nilainya jika ada rute spesifik yang dirasa OSRM kurang akurat
override_waktu = {
    ("BE", "DC"): 15.0, 
    ("DC", "BE"): 15.0
}

# 4. Looping pembuatan matriks per klaster
for klaster in klaster_list:
    df_klaster = df_puskesmas[df_puskesmas['Wilayah'].str.contains(klaster, case=False, na=False)].copy()
    
    # Gabungkan Depot (Indeks 0) dengan Puskesmas
    df_gabungan = pd.concat([pd.DataFrame([depot_row]), df_klaster]).reset_index(drop=True)
    
    jumlah_titik = len(df_gabungan)
    nama_lokasi = df_gabungan['Nama Puskesmas'].tolist()
    
    # Inisialisasi Matriks kosong
    matriks_waktu = np.zeros((jumlah_titik, jumlah_titik))
    
    # 5. Hitung waktu tempuh pakai OSRM
    for i in range(jumlah_titik):
        for j in range(jumlah_titik):
            if i == j:
                matriks_waktu[i][j] = 0.0
            else:
                nama_asal = df_gabungan.loc[i, 'Nama Puskesmas']
                nama_tujuan = df_gabungan.loc[j, 'Nama Puskesmas']
                
                # Cek apakah rute ini ada di daftar override manual
                if (nama_asal, nama_tujuan) in override_waktu:
                    matriks_waktu[i][j] = override_waktu[(nama_asal, nama_tujuan)]
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
                        # Durasi dari OSRM dalam satuan detik, kita ubah ke menit
                        durasi_detik = response['routes'][0]['duration']
                        durasi_menit = durasi_detik / 60
                        matriks_waktu[i][j] = round(durasi_menit, 2)
                    else:
                        print(f"⚠️ Gagal mencari rute {nama_asal} ke {nama_tujuan}")
                        matriks_waktu[i][j] = 999.0
                except Exception as e:
                    print(f"❌ Error API dari {nama_asal} ke {nama_tujuan}: {e}")
                    matriks_waktu[i][j] = 999.0
                
                # Jeda agar tidak kena block server OSRM
                time.sleep(0.2) 
                
    # 6. Simpan ke dalam DataFrame dan Export ke CSV
    df_matriks_waktu = pd.DataFrame(matriks_waktu, index=nama_lokasi, columns=nama_lokasi)
    file_waktu = f"{folder_output}matriks_waktu_{klaster.lower()}.csv"
    
    df_matriks_waktu.to_csv(file_waktu)
    print(f"✅ Matriks Waktu Klaster {klaster.upper()} selesai! ({jumlah_titik} titik)")

print("="*50)
print("🎉 SEMUA MATRIKS WAKTU BERHASIL DIBUAT!")