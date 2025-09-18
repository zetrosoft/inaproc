'''
Skrip untuk migrasi data Master Barang (Item) dari file CSV.
'''

import csv

import frappe

# Path absolut ke file CSV Anda
CSV_FILE_PATH = "/Users/user/Projects/custom-siumang/Material master.csv"

def migrate_items():
    print("Memulai migrasi data Barang (Item)...")

    company_name = "PT. SIUMANG TEMAN SUKSES"

    # Pemetaan akronim ke nama gudang grup yang diinginkan (sama seperti di migrate_warehouses.py)
    akronim_to_group_warehouse_map = {
        "INV": "Gudang RMPN",
        "FGH": "Finished Good",
        "WST": "Gudang Waste",
        "WIP": "Gudang Work In Process",
        "AST": "Gudang Umum",
        "ALL": "All Warehouses" # Untuk grup induk Item Group
    }

    try:
        with open(CSV_FILE_PATH, encoding='utf-8') as csvfile:
            # Menggunakan delimiter ; dan quotechar "
            reader = csv.DictReader(csvfile, delimiter=';')

            for row in reader:
                try:
                    # Ambil dan bersihkan data dari CSV
                    kode_barang = row.get('Kode Barang', '').strip()
                    nama_barang = row.get('Nama Barang', '').strip()
                    kategori_barang = row.get('Kategori Barang', '').strip()
                    satuan = row.get('Satuan', '').strip()
                    jenis_barang_csv = row.get('Jenis Barang', '').strip() # Ambil jenis barang dari CSV

                    # Lewati baris kosong atau tidak valid
                    if not all([kode_barang, nama_barang, kategori_barang, satuan, jenis_barang_csv]):
                        print(f"Data tidak lengkap pada baris: {row}, proses dilewati.")
                        continue

                    # Dapatkan akronim dari Item Group
                    akronim_prefix = frappe.db.get_value("Item Group", kategori_barang, "akronim")
                    if not akronim_prefix:
                        print(f"ERROR: Akronim tidak ditemukan untuk Item Group ''{kategori_barang}'' pada baris {reader.line_num}. Proses dilewati.")
                        continue

                    # Transformasi Item Code sesuai aturan
                    # 1. Pad dengan 0 hingga 6 digit
                    padded_kode = kode_barang.zfill(6)
                    # 2. Tambahkan prefix dari akronim Item Group
                    item_code = f"{akronim_prefix}-{padded_kode}"

                    # Periksa apakah item sudah ada
                    if frappe.db.exists("Item", {"item_code": item_code}):
                        print(f"Item ''{item_code}'' sudah ada, proses dilewati.")
                        continue

                    # --- Tentukan Gudang Default ---
                    default_warehouse_name = None
                    # Jika Item Group bukan grup induk dan memiliki akronim yang valid
                    if kategori_barang != "All Item Groups" and akronim_prefix in akronim_to_group_warehouse_map:
                        # Nama gudang leaf sama dengan Item Group
                        default_warehouse_name = kategori_barang

                        # Pastikan gudang leaf ini ada di database
                        # Frappe menambahkan suffix perusahaan ke nama gudang secara internal
                        # Jadi kita perlu mencari nama lengkapnya
                        full_default_warehouse_name = frappe.db.get_value(
                            "Warehouse",
                            {"warehouse_name": default_warehouse_name, "company": company_name},
                            "name"
                        )
                        if not full_default_warehouse_name:
                            print(f"Peringatan: Gudang default ''{default_warehouse_name}'' untuk Item Group ''{kategori_barang}'' tidak ditemukan. Item akan dibuat tanpa gudang default.")
                            default_warehouse_name = None # Set ke None jika tidak ditemukan
                        else:
                            default_warehouse_name = full_default_warehouse_name # Gunakan nama lengkap
                    else:
                        print(f"Peringatan: Item Group ''{kategori_barang}'' tidak memiliki gudang default yang sesuai. Item akan dibuat tanpa gudang default.")

                    # Buat dokumen Item baru
                    doc = frappe.get_doc({
                        "doctype": "Item",
                        "item_code": item_code,
                        "item_name": nama_barang,
                        "item_group": kategori_barang,
                        "stock_uom": satuan,
                        "is_stock_item": 1, # Sesuai Jenis Barang 'INV'
                        "allow_negative_stock": 0 # Default yang aman
                    })
                    doc.name = item_code # Secara eksplisit set nama dokumen
                    doc.naming_series = None # Set naming_series ke None untuk mencegah override

                    # Tambahkan Item Default jika gudang default ditemukan
                    if default_warehouse_name:
                        doc.append("item_defaults", {
                            "company": company_name,
                            "default_warehouse": default_warehouse_name
                        })

                    doc.insert(ignore_permissions=True)
                    print(f"Berhasil membuat Item: ''{item_code}'' - ''{nama_barang}''")

                except Exception as e:
                    print(f"Terjadi error pada baris {reader.line_num}: {row}")
                    print(f"Error: {e}")

    except FileNotFoundError:
        print(f"ERROR: File tidak ditemukan di '{CSV_FILE_PATH}'")
        return
    except Exception as e:
        print(f"Terjadi error saat membaca file CSV: {e}")
        return

    frappe.db.commit()
    print("\nMigrasi data Barang (Item) selesai.")

if __name__ == "__main__":
    migrate_items()
