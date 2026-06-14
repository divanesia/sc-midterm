import pandas as pd
import json
import os
from IPython.display import display

# =========================================================================
# FIX PATH: Mengunci posisi folder secara otomatis berdasarkan letak script
# =========================================================================
# BASE_DIR akan menghasilkan path absolut sampai ke folder 'eas/collab'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# path_collab langsung mengarah ke folder tempat script ini berada
path_collab = BASE_DIR

# path_json naik satu tingkat lalu masuk ke 'output_json'
path_json = os.path.join(os.path.dirname(BASE_DIR), 'output_json')
# =========================================================================

file_list = [
    'rute_ga.json', 
    'rute_ma.json', 
    'rute_dpso.json', 
    'rute_aco.json'
]

mapping_algo = {
    'rute_ga.json': 'GA',
    'rute_ma.json': 'MA',
    'rute_dpso.json': 'DPSO',
    'rute_aco.json': 'ACO'
}

data_komparasi = []

# 2. Proses Ekstraksi Data
for file_name in file_list:
    file_path = os.path.join(path_json, file_name)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            algo_name = mapping_algo.get(file_name, file_name.split('.')[0].upper())
            
            for klaster, hasil in data['hasil_per_klaster'].items():
                if not isinstance(hasil, dict) or 'statistik_10_run' not in hasil:
                    continue
                    
                stats = hasil['statistik_10_run']
                jarak_min = stats.get('fitness_minimum', hasil['total_jarak_semua_km'])
                
                data_komparasi.append({
                    'Algoritma': algo_name,
                    'Klaster': klaster,
                    'Total Kurir': hasil['total_kurir'],
                    'Jarak Min (KM)': jarak_min,
                    'Jarak Rata-rata (KM)': stats['fitness_rata_rata'],
                    'Std Deviasi': stats['fitness_std_dev'],
                    'Waktu Terbaik (Detik)': hasil['waktu_komputasi_detik_terbaik'],
                    'Waktu Rata-rata (Detik)': stats['waktu_komputasi_rata_rata_detik']
                })
    else:
        print(f"⚠️ Peringatan: File {file_name} tidak ditemukan!")

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
    
    df_jarak_summary = df_jarak_summary.rename(columns={'Std Deviasi': 'Rata-rata Std Deviasi'})
    df_jarak_summary['Jarak Min (KM)'] = df_jarak_summary['Jarak Min (KM)'].round(2)
    df_jarak_summary['Jarak Rata-rata (KM)'] = df_jarak_summary['Jarak Rata-rata (KM)'].round(2)
    df_jarak_summary['Rata-rata Std Deviasi'] = df_jarak_summary['Rata-rata Std Deviasi'].round(2)
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

    # Pastikan folder target eksis
    os.makedirs(path_collab, exist_ok=True)

    # Menyimpan file CSV langsung ke tempat script ini berada
    df_jarak_detail.to_csv(os.path.join(path_collab, "tabel_jarak_detail.csv"), index=False)
    df_jarak_summary.to_csv(os.path.join(path_collab, "tabel_jarak_summary.csv"), index=False)
    df_waktu_detail.to_csv(os.path.join(path_collab, "tabel_waktu_detail.csv"), index=False)
    df_waktu_summary.to_csv(os.path.join(path_collab, "tabel_waktu_summary.csv"), index=False)
    
    print(f"\n✅ Berhasil! 4 File CSV telah diperbarui di folder: {path_collab}")
    
else:
    print("❌ Gagal membuat tabel. Pastikan file JSON-nya ada ya!")