def aksi_admin(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()
    data = query.data

    if data == "kembali":
        list_order(query, context)
        return

    kode = context.user_data.get("kode")

    if not kode:
        query.message.reply_text("❌ Tidak ada kode")
        return

    if data == "aksi_timbang":
        context.user_data["berat"] = True
        query.message.reply_text("Masukkan berat (kg)")
        return

    status_map = {
        "aksi_proses": "🧼 Diproses",
        "aksi_antar": "🚀 Diantar",
        "aksi_selesai": "✅ Selesai"
    }

    status = status_map[data]

    cursor.execute("SELECT user_id FROM orders WHERE kode=?", (kode,))
    user_id = cursor.fetchone()[0]

    cursor.execute("UPDATE orders SET status=? WHERE kode=?", (status, kode))
    conn.commit()

    context.bot.send_message(user_id, f"""
📦 UPDATE LAUNDRY

Kode: {kode}
Status: {status}
""")

    query.message.reply_text("✅ Berhasil update")

# ==============================
# CEK STATUS USER
# ==============================

def cek_status(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    context.user_data["cek"] = True
    query.message.reply_text("Masukkan kode order")

# ==============================
# MAIN
# ==============================

def main():

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_command))

    dp.add_handler(CallbackQueryHandler(order, pattern="order"))
    dp.add_handler(CallbackQueryHandler(pilih_layanan, pattern="express|reguler|setrika"))
    dp.add_handler(CallbackQueryHandler(cek_status, pattern="cek"))

    dp.add_handler(CallbackQueryHandler(pilih_order, pattern="pilih_"))
    dp.add_handler(CallbackQueryHandler(aksi_admin, pattern="aksi_|kembali"))

    dp.add_handler(MessageHandler(Filters.location, alamat_maps))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
