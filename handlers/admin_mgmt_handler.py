from telegram import Update
from telegram.ext import ContextTypes
from utils.user_manager import require_role, Role, load_user_db, save_user_db, get_user_role
from utils.excel_manager import reset_excel_data

@require_role(Role.SUPERADMIN)
async def set_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]: return

    if len(context.args) < 2:
        await update.effective_message.reply_text("Format: `/setrole <user_id> <user_admin|user_input|viewer>`", parse_mode="Markdown")
        return

    try:
        user_id = int(context.args[0])
        role = context.args[1].lower()
    except ValueError:
        return await update.effective_message.reply_text("User ID harus angka.")

    if role not in ["user_admin", "user_input", "viewer"]:
        return await update.effective_message.reply_text("Role tidak valid.")

    db = load_user_db()
    chat_str = str(chat.id)
    if chat_str not in db["groups"]: db["groups"][chat_str] = {"user_admins": [], "user_inputs": []}

    for key in ["user_admins", "user_inputs"]:
        if user_id in db["groups"][chat_str][key]:
            db["groups"][chat_str][key].remove(user_id)

    if role == "user_admin": db["groups"][chat_str]["user_admins"].append(user_id)
    elif role == "user_input": db["groups"][chat_str]["user_inputs"].append(user_id)

    save_user_db(db)
    await update.effective_message.reply_text(f"✅ User {user_id} diset sebagai {role.upper()}")


async def check_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        await update.effective_message.reply_text("Perintah ini hanya dapat dijalankan di dalam grup.")
        return

    current_role = get_user_role(chat.id, user.id)

    pesan = (
        f"👤 <b>Informasi Akses Anda</b>\n\n"
        f"🔹 <b>Nama:</b> {user.full_name}\n"
        f"🔹 <b>ID Telegram:</b> <code>{user.id}</code>\n"
        f"🔹 <b>Level Akses:</b> <b>{current_role.name}</b>\n"
    )

    try:
        await update.effective_message.reply_text(pesan, parse_mode="HTML")
    except Exception as e:
        print(f"Gagal mengirim pesan /cekakses: {e}")

async def get_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.reply_to_message:
        target_user = update.effective_message.reply_to_message.from_user
        pesan = f"👤 ID {target_user.full_name}: `{target_user.id}`"
    else:
        user = update.effective_user
        pesan = f"👤 ID Anda ({user.full_name}): `{user.id}`"

    await update.effective_message.reply_text(pesan, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        "🤖 <b>Menu Bantuan BotFevagroup</b> 🤖\n"
        "Berikut adalah daftar perintah berdasarkan Hak Akses:\n\n"

        "🟢 <b>UMUM (Semua Anggota / Viewer)</b>\n"
        "• <code>/help</code> atau <code>/menu</code> : Menampilkan pesan ini\n"
        "• <code>/cekakses</code> : Mengetahui level akses Anda saat ini\n"
        "• <code>/id</code> : Melihat ID Telegram (Ketik langsung atau reply pesan orang)\n"
        "• <code>/getlogs</code> : Mengunduh file Excel log grup ini\n\n"

        "🟡 <b>USER INPUT (Pencatat Harian)</b>\n"
        "• <b>Tambah log:</b>\n"
        "  <code>/+ [DDMMYYYY] keterangan_log [deskripsi tambahan]</code>\n"
        "• <b>Edit log:</b>\n"
        "  <code>/e &lt;no_baris&gt; keterangan_baru [deskripsi tambahan]</code>\n"
        "• <b>Hapus log:</b>\n"
        "  <code>/- &lt;no_baris&gt;</code>\n"
        "• User Input hanya dapat menambah, mengedit, dan menghapus data pada hari yang sama.\n\n"

        "🟠 <b>ADMIN GRUP (User Admin)</b>\n"
        "• <code>/setup</code> : Inisialisasi grup dan membuat file Excel baru\n"
        "• Dapat menambah, mengedit, dan menghapus data tanpa batasan hari.\n\n"

        "🔴 <b>SUPERADMIN</b>\n"
        "• <code>/setrole</code> : Mengubah hak akses pengguna.\n"
        "  <i>Format: /setrole &lt;User_ID&gt; &lt;user_admin|user_input|viewer&gt;</i>\n"
        "• <code>/resetdatabase</code> : Menghapus data.\n"
        "  <i>Format: /resetdatabase &lt;excel&gt;</i>"
    )

    await update.effective_message.reply_text(pesan, parse_mode="HTML")


@require_role(Role.SUPERADMIN)
async def reset_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    if not args or args[0].lower() != "excel":
        pesan = (
            "⚠️ *PERINGATAN: TINDAKAN BERBAHAYA (SUPERADMIN ONLY)* ⚠️\n\n"
            "Perintah ini akan menghapus data secara permanen. "
            "Gunakan `/resetdatabase excel` untuk menghapus semua riwayat log di Excel grup ini (Header dipertahankan)."
        )
        return await update.effective_message.reply_text(pesan, parse_mode="Markdown")

    sukses, pesan = await reset_excel_data(chat.id)
    await update.effective_message.reply_text(f"📊 *Reset Excel Grup:*\n{pesan}", parse_mode="Markdown")
