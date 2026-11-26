import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config.settings import BOT_TOKEN
from handlers.setup_handler import setup_command
from handlers.export_handler import get_logs_command
from handlers.log_handler import auto_log_message
from handlers.admin_mgmt_handler import (
    set_role_command, check_role_command, get_id_command,
    help_command, reset_database_command
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Onboarding & Hak Akses
    app.add_handler(CommandHandler("setup", setup_command))
    app.add_handler(CommandHandler("resetdatabase", reset_database_command))
    app.add_handler(CommandHandler("setrole", set_role_command))
    app.add_handler(CommandHandler("cekakses", check_role_command))
    app.add_handler(CommandHandler("id", get_id_command))

    # Logger otomatis untuk pesan yang diawali '+'
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_log_message))

    # Unduh Berkas
    app.add_handler(CommandHandler("getlogs", get_logs_command))

    # Bantuan & Menu
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", help_command))

    logging.info("BotFevagroup Asynchronous berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
