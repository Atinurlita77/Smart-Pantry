import sqlite3
from pathlib import Path
from datetime import date, timedelta
from contextlib import contextmanager

# Path database SQLite konsisten pada direktori utama PantryPal
DB_PATH = Path(__file__).resolve().parent / "foodsy.db"


@contextmanager
def get_db():
    """
    Context manager untuk koneksi SQLite.
    Memastikan commit saat sukses, rollback jika error,
    dan selalu menutup koneksi (conn.close()) pada blok finally.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Inisialisasi tabel SQLite (inventory, shopping, app_meta).
    Memasukkan seed/default data HANYA jika inisialisasi pertama kali.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Tabel inventory untuk My Pantry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                qty TEXT NOT NULL,
                expiry TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabel shopping untuk Shopping List
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabel metadata untuk melacak inisialisasi awal (mencegah seed ganda)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Cek apakah seed data sudah pernah dimasukkan
        cursor.execute("SELECT value FROM app_meta WHERE key = 'seeded'")
        seeded = cursor.fetchone()

        if not seeded:
            # Seed awal untuk inventory
            seed_inventory = [
                ("Telur", "6 butir", (date.today() + timedelta(days=8)).isoformat()),
                ("Susu", "1 liter", (date.today() + timedelta(days=3)).isoformat()),
                ("Wortel", "3 buah", (date.today() + timedelta(days=6)).isoformat()),
            ]
            cursor.executemany(
                "INSERT INTO inventory (name, qty, expiry) VALUES (?, ?, ?)",
                seed_inventory
            )

            # Seed awal untuk shopping list
            seed_shopping = [
                ("Bawang putih",),
                ("Minyak goreng",),
            ]
            cursor.executemany(
                "INSERT INTO shopping (name) VALUES (?)",
                seed_shopping
            )

            cursor.execute("INSERT INTO app_meta (key, value) VALUES ('seeded', '1')")


# -------------------- OPERASI INVENTORY --------------------

def get_inventory():
    """
    Mengambil seluruh bahan dari tabel inventory.
    Kolom expiry dikonversi menjadi datetime.date untuk kompatibilitas UI.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, qty, expiry FROM inventory ORDER BY id ASC")
        rows = cursor.fetchall()
        items = []
        for r in rows:
            exp_val = r["expiry"]
            if isinstance(exp_val, str):
                try:
                    exp_date = date.fromisoformat(exp_val)
                except ValueError:
                    exp_date = date.today()
            elif isinstance(exp_val, date):
                exp_date = exp_val
            else:
                exp_date = date.today()

            items.append({
                "id": r["id"],
                "name": r["name"],
                "qty": r["qty"],
                "expiry": exp_date,
            })
        return items


def add_inventory_item(name: str, qty: str, expiry) -> int:
    """
    Menambahkan bahan baru ke tabel inventory.
    """
    exp_str = expiry.isoformat() if hasattr(expiry, "isoformat") else str(expiry)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventory (name, qty, expiry) VALUES (?, ?, ?)",
            (name.strip().title(), qty.strip(), exp_str)
        )
        return cursor.lastrowid


def update_inventory_item(item_id: int, qty: str, expiry) -> bool:
    """
    Memperbarui jumlah dan tanggal kedaluwarsa bahan berdasarkan ID.
    """
    exp_str = expiry.isoformat() if hasattr(expiry, "isoformat") else str(expiry)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET qty = ?, expiry = ? WHERE id = ?",
            (qty.strip(), exp_str, item_id)
        )
        return cursor.rowcount > 0


def delete_inventory_item(item_id: int) -> bool:
    """
    Menghapus bahan dari tabel inventory berdasarkan ID.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        return cursor.rowcount > 0


# -------------------- OPERASI SHOPPING LIST --------------------

def get_shopping():
    """
    Mengambil seluruh item belanja dari tabel shopping.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM shopping ORDER BY id ASC")
        rows = cursor.fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]


def add_shopping_item(name: str) -> int:
    """
    Menambahkan item belanja baru ke tabel shopping.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO shopping (name) VALUES (?)",
            (name.strip().title(),)
        )
        return cursor.lastrowid


def delete_shopping_item(item_id: int) -> bool:
    """
    Menghapus item belanja dari tabel shopping berdasarkan ID.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping WHERE id = ?", (item_id,))
        return cursor.rowcount > 0
