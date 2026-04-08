 context.bot.send_message(ADMIN_ID, f"""
🔔 ORDER BARU

Kode: {kode}
Nama: {user.first_name}
Layanan: {layanan}

📍 {link_maps}
""")

    context.user_data.clear()

# ==============================
# ORDER MANUAL (TEXT)
# ==============================

def handle_text(update: Update, context: CallbackContext):

    text = update.message.text
    user = update.message.from_user

    # ==============================
    # ADMIN MENU
    # ==============================

    if text == "📊 Lihat Order":
        list_order(update, context)
        return

    if text == "🏠 Menu":
        context.user_data.clear()
        update.message.reply_text("Kembali ke menu utama", reply_markup=user_menu())
        return

    # ==============================
    # INPUT BERAT (ADMIN)
    # ==============================

    if "berat" in context.user_data:

        kode = context.user_data["kode"]
        berat = float(text)

        cursor.execute("SELECT layanan,user_id FROM orders WHERE kode=?", (kode,))
        layanan, user_id = cursor.fetchone()

        if layanan == "express":
            harga = berat * 9000
        elif layanan == "reguler":
            harga = berat * 6500
        else:
            harga = berat * 3000

        cursor.execute("""
        UPDATE orders SET berat=?, harga=?, status=?
        WHERE kode=?
        """, (berat, harga, "⚖️ Ditimbang", kode))

        conn.commit()

        context.bot.send_message(user_id, f"""
📦 Laundry ditimbang

Berat: {berat} kg
Total: Rp{int(harga)}
""")

        update.message.reply_text("✅ Berhasil ditimbang", reply_markup=admin_keyboard())
        context.user_data.clear()
        return