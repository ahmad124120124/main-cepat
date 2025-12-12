import pandas as pd
import datetime
import os

DATA_DIR = 'data'

def init_data():
    """Menginisialisasi atau memuat DataFrames dari file CSV."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
       
    def load_or_create(filename, columns, dtypes=None):
        path = os.path.join(DATA_DIR, filename)
        try:
            df = pd.read_csv(path)
            if dtypes:
                for col, dtype in dtypes.items():
                    if dtype == 'int':
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    elif dtype == 'datetime':
                        df[col] = pd.to_datetime(df[col], errors='coerce')
        except FileNotFoundError:
            df = pd.DataFrame(columns=columns)
            if dtypes:
                for col, dtype in dtypes.items():
                    if dtype == 'int':
                        df[col] = df[col].astype(int) if col in df.columns else []
                    elif dtype == 'datetime':
                        df[col] = pd.to_datetime(df[col]) if col in df.columns else []
        return df

    buku_df = load_or_create(
        'buku.csv',
        ['ID_Buku', 'Judul', 'Penulis', 'Tahun_Terbit', 'Jumlah_Stok'],
        {'ID_Buku': 'int', 'Tahun_Terbit': 'int', 'Jumlah_Stok': 'int'}
    )
   
    anggota_df = load_or_create(
        'anggota.csv',
        ['ID_Anggota', 'Nama', 'Alamat', 'No_Telp'],
        {'ID_Anggota': 'int'}
    )
   
    pinjam_df = load_or_create(
        'peminjaman.csv',
        ['ID_Pinjam', 'ID_Buku', 'ID_Anggota', 'Tanggal_Pinjam', 'Tanggal_Kembali', 'Status'],
        {'ID_Pinjam': 'int', 'ID_Buku': 'int', 'ID_Anggota': 'int', 'Tanggal_Pinjam': 'datetime', 'Tanggal_Kembali': 'datetime'}
    )
   
    return buku_df, anggota_df, pinjam_df

def save_data(buku_df, anggota_df, pinjam_df):
    """Menyimpan DataFrames ke file CSV."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
       
    buku_df.to_csv(os.path.join(DATA_DIR, 'buku.csv'), index=False)
    anggota_df.to_csv(os.path.join(DATA_DIR, 'anggota.csv'), index=False)
    pinjam_df.to_csv(os.path.join(DATA_DIR, 'peminjaman.csv'), index=False)


def get_new_id(df, id_col):
    """Mendapatkan ID baru yang unik."""
    return df[id_col].max() + 1 if not df.empty else 1


def pinjam_buku(buku_df, anggota_df, pinjam_df, id_buku, id_anggota, tgl_pinjam):
    """Mencatat peminjaman buku."""
    if id_buku not in buku_df['ID_Buku'].values:
        return False, "ID Buku tidak ditemukan."
    if id_anggota not in anggota_df['ID_Anggota'].values:
        return False, "ID Anggota tidak ditemukan."

    buku_idx = buku_df[buku_df['ID_Buku'] == id_buku].index[0]
    stok = buku_df.loc[buku_idx, 'Jumlah_Stok']
   
    if stok <= 0:
        return False, "Stok buku habis."

    buku_df.loc[buku_idx, 'Jumlah_Stok'] -= 1
   
    new_id_pinjam = get_new_id(pinjam_df, 'ID_Pinjam')
    new_row = pd.DataFrame([{
        'ID_Pinjam': new_id_pinjam,
        'ID_Buku': id_buku,
        'ID_Anggota': id_anggota,
        'Tanggal_Pinjam': pd.to_datetime(tgl_pinjam),
        'Tanggal_Kembali': pd.NaT,
        'Status': 'Dipinjam'
    }])
    pinjam_df = pd.concat([pinjam_df, new_row], ignore_index=True)
   
    return True, f"Peminjaman berhasil. ID Pinjam: {new_id_pinjam}", buku_df, pinjam_df

def kembalikan_buku(buku_df, pinjam_df, id_pinjam, tgl_kembali):
    """Mencatat pengembalian buku."""
    if id_pinjam not in pinjam_df['ID_Pinjam'].values:
        return False, "ID Peminjaman tidak ditemukan."
       
    pinjam_idx = pinjam_df[pinjam_df['ID_Pinjam'] == id_pinjam].index[0]
    status = pinjam_df.loc[pinjam_idx, 'Status']
   
    if status == 'Kembali':
        return False, "Buku sudah dikembalikan sebelumnya."
       
    id_buku = pinjam_df.loc[pinjam_idx, 'ID_Buku']
    buku_idx = buku_df[buku_df['ID_Buku'] == id_buku].index[0]
   
    buku_df.loc[buku_idx, 'Jumlah_Stok'] += 1
   
    pinjam_df.loc[pinjam_idx, 'Status'] = 'Kembali'
    pinjam_df.loc[pinjam_idx, 'Tanggal_Kembali'] = pd.to_datetime(tgl_kembali)
   
    return True, f"Pengembalian berhasil. Buku: {buku_df.loc[buku_idx, 'Judul']}", buku_df, pinjam_df