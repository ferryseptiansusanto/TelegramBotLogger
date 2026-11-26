import os
import re
import json
import asyncio
import shutil
from datetime import datetime
from openpyxl import Workbook, load_workbook
from config.settings import DATA_DIR, GROUP_REGISTRY_FILE

excel_lock = asyncio.Lock()

HEADER = ["Timestamp", "User ID", "Username", "Nama Lengkap", "User Level", "Keterangan", "Detail"]


def sanitize_filename(name: str) -> str:
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean_name or "Unnamed_Group"


def load_registry() -> dict:
    if not os.path.exists(GROUP_REGISTRY_FILE):
        return {}
    try:
        with open(GROUP_REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_registry(registry: dict):
    with open(GROUP_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def get_filepath(chat_id: int) -> str | None:
    filename = load_registry().get(str(chat_id))
    return os.path.join(DATA_DIR, filename) if filename else None


async def setup_excel(chat_id: int, group_title: str) -> str:
    async with excel_lock:
        registry = load_registry()
        filename = f"{sanitize_filename(group_title)}.xlsx"
        filepath = os.path.join(DATA_DIR, filename)

        if not os.path.exists(filepath):
            wb = Workbook()
            ws = wb.active
            ws.title = "Activity Logs"
            ws.append(HEADER)
            wb.save(filepath)

        registry[str(chat_id)] = filename
        save_registry(registry)
        return filepath


async def append_data(chat_id: int, user_id: int, username: str, full_name: str, level: str, tipe_trx: str, keterangan: str,
                      satuan: str, jumlah: str, detail: str = "-", custom_timestamp: str = None) -> tuple[bool, int]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, 0

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active

        # Gunakan custom_timestamp jika pengguna memberikan input @DDMMYYYY, jika tidak gunakan waktu sekarang
        timestamp = custom_timestamp if custom_timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ws.append([
            timestamp,
            str(user_id),
            f"@{username}" if username else "-",
            full_name,
            level,
            keterangan,
            detail
        ])
        wb.save(filepath)

        # MENGEMBALIKAN ID BARIS: (Baris Excel - 1)
        user_row_id = ws.max_row - 1
        return True, user_row_id


async def edit_logger_data(chat_id: int, row: int, keterangan: str, detail: str,
                           require_same_day: bool = False) -> tuple[bool, str]:
    """Edit only the logger text (Keterangan) and additional detail for a row."""
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan."

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active

        excel_row = row + 1
        if excel_row <= 1 or excel_row > ws.max_row:
            return False, f"Nomor baris tidak valid. Saat ini hanya ada data baris 1 sampai {ws.max_row - 1}."

        if require_same_day:
            cell_value = ws.cell(row=excel_row, column=1).value
            if not cell_value:
                return False, "Baris yang dipilih tidak memiliki data tanggal."

            try:
                if isinstance(cell_value, datetime):
                    entry_date = cell_value.date()
                else:
                    entry_date = datetime.strptime(str(cell_value).strip(), "%Y-%m-%d %H:%M:%S").date()

                current_date = datetime.now().date()
                if entry_date != current_date:
                    return False, "User Input hanya dapat mengedit data pada hari yang sama."
            except Exception:
                return False, "Format tanggal pada baris tersebut tidak dapat divalidasi."

        ws.cell(row=excel_row, column=6, value=keterangan)
        ws.cell(row=excel_row, column=7, value=detail)
        wb.save(filepath)

        return True, "Sukses"


async def delete_logger_data(chat_id: int, row: int, require_same_day: bool = False) -> tuple[bool, str]:
    """Delete a logger row, optionally enforcing same-day restriction."""
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan."

    async with excel_lock:
        wb = load_workbook(filepath)
        ws = wb.active

        excel_row = row + 1
        if excel_row <= 1 or excel_row > ws.max_row:
            return False, f"Nomor baris tidak valid. Saat ini hanya ada data baris 1 sampai {ws.max_row - 1}."

        if require_same_day:
            cell_value = ws.cell(row=excel_row, column=1).value
            if not cell_value:
                return False, "Baris yang dipilih tidak memiliki data tanggal."

            try:
                if isinstance(cell_value, datetime):
                    entry_date = cell_value.date()
                else:
                    entry_date = datetime.strptime(str(cell_value).strip(), "%Y-%m-%d %H:%M:%S").date()

                current_date = datetime.now().date()
                if entry_date != current_date:
                    return False, "User Input hanya dapat menghapus data pada hari yang sama."
            except Exception:
                return False, "Format tanggal pada baris tersebut tidak dapat divalidasi."

        ws.delete_rows(excel_row)
        wb.save(filepath)

        return True, "Sukses"


async def reset_excel_data(chat_id: int) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log Excel tidak ditemukan. Gunakan /setup terlebih dahulu."

    async with excel_lock:
        try:
            wb = load_workbook(filepath)

            # 1. Dapatkan nama sheet yang aktif (misal: "Activity Logs")
            active_sheet_name = wb.active.title

            # 2. Buat sheet baru sementara terlebih dahulu (agar workbook tidak pernah kosong)
            ws_new = wb.create_sheet(title="Temp_Logs")

            # 3. Hapus sheet lama
            del wb[active_sheet_name]

            # 4. Ubah nama sheet baru menjadi nama sheet aslinya
            ws_new.title = active_sheet_name
            ws = wb.active

            # 5. Tulis ulang Header format terbaru
            ws.append(HEADER)

            wb.save(filepath)
            return True, "Berhasil mereset Excel."

        except Exception as e:
            return False, f"Terjadi kesalahan saat mereset Excel: {e}"


async def generate_export_file(chat_id: int) -> tuple[bool, str]:
    filepath = get_filepath(chat_id)
    if not filepath or not os.path.exists(filepath):
        return False, "File log tidak ditemukan. Pastikan /setup sudah dijalankan."

    export_path = filepath.replace(".xlsx", "_Export.xlsx")

    async with excel_lock:
        try:
            shutil.copy2(filepath, export_path)
            return True, export_path
        except Exception as e:
            return False, str(e)
