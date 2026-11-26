import re
from datetime import datetime

def parse_logger_input(raw_text: str) -> tuple[bool, str, str, str, str]:
    """
    Parses a logger message in the format:
        + [DDMMYYYY] data_logger_text [additional description]
    or
        add [DDMMYYYY] data_logger_text [additional description]

    Both bracket parts are optional. If the date is missing or invalid,
    today's date is used.

    Returns:
        (success, custom_ts, log_text, additional_desc, error_msg)
    """
    text = raw_text.strip()
    if not text:
        return False, "", "", "", "Pesan kosong."

    # Prefix: '+' or 'add'
    match = re.match(r'^(?:\+|add)\s*', text, re.IGNORECASE)
    if not match:
        return False, "", "", "", "Pesan logger harus diawali '+' atau 'add'."

    content = text[match.end():].strip()
    if not content:
        return False, "", "", "", "Tidak ada teks logger setelah prefix."

    # Optional date at the beginning: [DDMMYYYY]
    date_match = re.match(r'^\[(\d{8})\]\s*(.*)$', content)
    custom_ts = None
    if date_match:
        date_str = date_match.group(1)
        content = date_match.group(2).strip()
        try:
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = int(date_str[4:8])
            # Validate actual calendar date
            custom_ts = datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            return False, "", "", "", "Format tanggal tidak valid. Gunakan format DDMMYYYY (contoh: 26112026)."
    else:
        custom_ts = datetime.now().strftime("%Y-%m-%d")

    # Optional additional description at the end: [additional description]
    additional_desc = ""
    desc_match = re.search(r'\s*\[(.*?)\]\s*$', content)
    if desc_match:
        additional_desc = desc_match.group(1).strip()
        content = content[:desc_match.start()].strip()

    log_text = content.strip()
    if not log_text:
        return False, "", "", "", "Teks logger kosong."

    return True, custom_ts, log_text, additional_desc, ""


def parse_edit_command(raw_text: str) -> tuple[bool, int, str, str, str]:
    """
    Parses an edit command.

    Supported formats:
        edit <row> <new text> [additional description]
        e <row> <new text> [additional description]

    Returns:
        (success, row, new_text, additional_desc, error_msg)
    """
    text = raw_text.strip()
    match = re.match(r'^(?:edit|e)\s+', text, re.IGNORECASE)
    if not match:
        return False, 0, "", "", "Perintah edit harus diawali 'e' atau 'edit'."

    body = text[match.end():].strip()
    if not body:
        return False, 0, "", "", "Format edit: edit <row> <teks_baru> [deskripsi tambahan]"

    parts = body.split(maxsplit=1)
    row_part = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    try:
        row = int(row_part)
    except ValueError:
        return False, 0, "", "", "Nomor baris harus angka."
    if row <= 0:
        return False, 0, "", "", "Nomor baris harus lebih dari 0."

    if not rest:
        return False, 0, "", "", "Teks baru tidak boleh kosong."

    # Optional additional description at the end: [description]
    additional_desc = ""
    desc_match = re.search(r'\s*\[(.*?)\]\s*$', rest)
    if desc_match:
        additional_desc = desc_match.group(1).strip()
        rest = rest[:desc_match.start()].strip()

    new_text = rest.strip()
    if not new_text:
        return False, 0, "", "", "Teks baru tidak boleh kosong."

    return True, row, new_text, additional_desc, ""


def parse_delete_command(raw_text: str) -> tuple[bool, int, str]:
    """
    Parses a delete command.

    Supported formats:
        d <row>
        del <row>
        delete <row>
        -<row>
        - <row>

    Returns:
        (success, row, error_msg)
    """
    text = raw_text.strip()

    # Handle '-' separately so '-5' works without a space
    if text.startswith("-"):
        body = text[1:].strip()
    else:
        match = re.match(r'^(?:delete|del|d)\s+', text, re.IGNORECASE)
        if not match:
            return False, 0, "Perintah hapus harus diawali 'd', 'del', 'delete', atau '-'."
        body = text[match.end():].strip()

    if not body:
        return False, 0, "Format hapus: d <row> atau - <row>"

    row_part = body.split(maxsplit=1)[0]
    try:
        row = int(row_part)
    except ValueError:
        return False, 0, "Nomor baris harus angka."

    if row <= 0:
        return False, 0, "Nomor baris harus lebih dari 0."

    return True, row, ""
