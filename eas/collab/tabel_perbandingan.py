import pandas as pd
import json
import os
from IPython.display import display

# 1. Konfigurasi Path Input (JSON) dan Output (CSV di folder collab)
path_json = r'C:\diva\1TS\6\sc\midterm\eas\output_json'
path_collab = r'C:\diva\1TS\6\sc\midterm\eas\collab'  

file_list = [
    'rute_ga.json', 
    'rute_ma.json', 
    'rute_dpso.json', 
    'rute_aco.json'
]

# Dictionary untuk memaksa nama algoritma menjadi singkatan pendek
mapping_algo = {
    'rute_ga.json': 'GA',
    'rute_ma.json': 'MA',
    'rute_dpso.json': 'DPSO',
    'rute_aco.json': 'ACO'
}

data_komparasi = []

# 2. Proses Ekstraksi Data dari ke-4 File JSON
for file_name in file_list:
    file_path = os.path.join(path_json, file_name)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            
            # Ambil singkatan pendek berdasarkan nama file-nya
            algo_name = mapping_algo.get(file_name, file_name.split('.')[0].upper())
            
            for klaster, hasil in data['hasil_per_klaster'].items():
                stats = hasil['statistik_10_run']
                
                data_komparasi.append({
                    'Algoritma': algo_name,
                    'Klaster': klaster,
                    'Total Kurir': hasil['total_kurir'],
                    'Jarak Min (KM)': stats['fitness_minimum'],
                    'Jarak Rata-rata (KM)': stats['fitness_rata_rata'],
                    'Std Deviasi': stats['fitness_std_dev'],
                    'Waktu Terbaik (Detik)': hasil['waktu_komputasi_detik_terbaik'],
                    'Waktu Rata-rata (Detik)': stats['waktu_komputasi_rata_rata_detik']
                })
else:
    if not os.path.exists(file_path):
        print(f"⚠️ Peringatan: File {file_name} tidak ditemukan di folder {path_json}!")

# 3. Buat DataFrame dan Pisahkan Tabel
if len(data_komparasi) > 0:
    df_all = pd.DataFrame(data_komparasi)
    df_all_sorted = df_all.sort_values(by=['Klaster', 'Algoritma']).reset_index(drop=True)

    # ==========================================
    # BAGIAN 1: TABEL KOMPARASI JARAK & ARMADA
    # ==========================================
    kolom_jarak = ['Algoritma', 'Klaster', 'Total Kurir', 'Jarak Min (KM)', 'Jarak Rata-rata (KM)', 'Std Deviasi']
    df_jarak_detail = df_all_sorted[kolom_jarak]
    
    print("=== TABEL 1A: RINCIAN JARAK & ARMADA (PER KLASTER) ===")
    display(df_jarak_detail)

    print("\n=== TABEL 1B: GRAND TOTAL JARAK & ARMADA (SE-SURABAYA) ===")
    df_jarak_summary = df_all.groupby('Algoritma').agg({
        'Total Kurir': 'sum',
        'Jarak Min (KM)': 'sum',
        'Jarak Rata-rata (KM)': 'sum',
        'Std Deviasi': 'mean'
    }).reset_index().sort_values(by='Jarak Min (KM)').reset_index(drop=True)
    
    df_jarak_summary['Jarak Min (KM)'] = df_jarak_summary['Jarak Min (KM)'].round(2)
    df_jarak_summary['Jarak Rata-rata (KM)'] = df_jarak_summary['Jarak Rata-rata (KM)'].round(2)
    df_jarak_summary['Std Deviasi'] = df_jarak_summary['Std Deviasi'].round(2)
    display(df_jarak_summary)

    # ==========================================
    # BAGIAN 2: TABEL KOMPARASI WAKTU KOMPUTASI
    # ==========================================
    kolom_waktu = ['Algoritma', 'Klaster', 'Waktu Terbaik (Detik)', 'Waktu Rata-rata (Detik)']
    df_waktu_detail = df_all_sorted[kolom_waktu]

    print("\n=== TABEL 2A: RINCIAN WAKTU KOMPUTASI (PER KLASTER) ===")
    display(df_waktu_detail)

    print("\n=== TABEL 2B: TOTAL WAKTU KOMPUTASI (SE-SURABAYA) ===")
    df_waktu_summary = df_all.groupby('Algoritma').agg({
        'Waktu Terbaik (Detik)': 'sum',
        'Waktu Rata-rata (Detik)': 'sum'
    }).reset_index().sort_values(by='Waktu Rata-rata (Detik)').reset_index(drop=True)
    
    df_waktu_summary['Waktu Terbaik (Detik)'] = df_waktu_summary['Waktu Terbaik (Detik)'].round(2)
    df_waktu_summary['Waktu Rata-rata (Detik)'] = df_waktu_summary['Waktu Rata-rata (Detik)'].round(2)
    display(df_waktu_summary)

    # Menyimpan file CSV ke folder collab
    df_jarak_detail.to_csv(f"{path_collab}\\tabel_jarak_detail.csv", index=False)
    df_jarak_summary.to_csv(f"{path_collab}\\tabel_jarak_summary.csv", index=False)
    df_waktu_detail.to_csv(f"{path_collab}\\tabel_waktu_detail.csv", index=False)
    df_waktu_summary.to_csv(f"{path_collab}\\tabel_waktu_summary.csv", index=False)
    
    print(f"\n✅ Berhasil! 4 File CSV dengan nama algoritma pendek telah diperbarui di folder 'collab'")
    
else:
    print("❌ Gagal membuat tabel. Pastikan file JSON-nya ada ya!")