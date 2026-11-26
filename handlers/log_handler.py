from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import get_user_role, Role
from utils.excel_manager import append_data, edit_logger_data, delete_logger_data
from utils.text_parser import parse_logger_input, parse_edit_command, parse_delete_command

async def auto_log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    # Pastikan pesan berupa teks terlebih dahulu
    if not message or not message.text:
        return

    # Logger hanya tersedia di dalam grup
    if not chat or chat.type not in ["group", "supergroup"]:
        await message.reply_text("❌ Perintah logger hanya dapat digunakan di dalam grup.")
        return

    if not user:
        return

    text = message.text.strip()
    if not text:
        return

    # STANDARDISASI: semua command logger harus diawali "/"
    if not text.startswith("/"):
        return

    # Hapus prefix "/" untuk diproses sebagai perintah logger
    text = text[1:].strip()

    role = get_user_role(chat.id, user.id)

    # ADD command: "/+" atau "/add"
    if text.startswith("+") or text.lower().startswith("add"):
        sukses, custom_ts, log_text, additional_desc, err_msg = parse_logger_input(text)
        if not sukses:
            await message.reply_text(f"❌ {err_msg}")
            return

        # Jika user_input, hanya boleh menambah log untuk tanggal hari ini
        if role == Role.USER_INPUT:
            today = datetime.now().strftime("%Y-%m-%d")
            if custom_ts != today:
                await message.reply_text("⛔ User Input hanya dapat menambah log untuk tanggal hari ini.")
                return

        sukses_append, row_id = await append_data(
            chat_id=chat.id,
            user_id=user.id,
            username=user.username or "",
            full_name=user.full_name,
            level=role.name,
            tipe_trx="-",
            keterangan=log_text,
            satuan="-",
            jumlah="-",
            detail=additional_desc,
            custom_timestamp=custom_ts
        )

        if not sukses_append:
            await message.reply_text("❌ Gagal menyimpan log. Pastikan /setup sudah dijalankan oleh Admin grup.")
            return

        await message.reply_text(f"✅ Log berhasil disimpan (baris {row_id}).")
        return

    # EDIT command: "/e" atau "/edit"
    if text.lower().startswith(("edit", "e ")):
        if role < Role.USER_INPUT:
            await message.reply_text("⛔ Akses ditolak. Anda tidak memiliki izin untuk mengedit data.")
            return

        sukses, row, new_text, new_desc, err_msg = parse_edit_command(text)
        if not sukses:
            await message.reply_text(f"❌ {err_msg}")
            return

        require_same_day = (role == Role.USER_INPUT)
        sukses, pesan = await edit_logger_data(
            chat.id,
            row,
            new_text,
            new_desc,
            require_same_day=require_same_day
        )
        await message.reply_text(pesan)
        return

    # DELETE command: "/-" atau "/del" dan seterusnya
    if text.lower().startswith(("del", "d ", "delete", "-")):
        if role < Role.USER_INPUT:
            await message.reply_text("⛔ Akses ditolak. Anda tidak memiliki izin untuk menghapus data.")
            return

        sukses, row, err_msg = parse_delete_command(text)
        if not sukses:
            await message.reply_text(f"❌ {err_msg}")
            return

        require_same_day = (role == Role.USER_INPUT)
        sukses, pesan = await delete_logger_data(
            chat.id,
            row,
            require_same_day=require_same_day
        )
        await message.reply_text(pesan)
        return

    # Bukan perintah logger
    return
