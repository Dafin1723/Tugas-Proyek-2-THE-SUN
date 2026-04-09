<<<<<<< HEAD
from multiprocessing import context

from bot_Laundry import generate_kode


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

    if "layanan" in context.user_data:

        kode = generate_kode()

        cursor.execute("""
        INSERT INTO orders(kode,user_id,nama,layanan,alamat,status,tanggal)
        VALUES(?,?,?,?,?,?,?)
        """, (
            kode, user.id, user.first_name,
            context.user_data["layanan"],
            text, "🚚 Menunggu dijemput",
            datetime.now().strftime("%d-%m-%Y")
        ))

        conn.commit()

        update.message.reply_text(f"✅ Order berhasil\nKode: {kode}")
        context.user_data.clear()

# ==============================
# ADMIN PRO SYSTEM
# ==============================

def list_order(update: Update, context: CallbackContext):

    cursor.execute("SELECT kode,nama,status FROM orders ORDER BY id DESC LIMIT 10")
    data = cursor.fetchall()

    if not data:
        update.message.reply_text("Belum ada order")
        return

    keyboard = [
        [InlineKeyboardButton(f"{d[0]} - {d[1]} ({d[2]})", callback_data=f"pilih_{d[0]}")]
        for d in data
    ]

    update.message.reply_text(
        "📊 Pilih Order:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def pilih_order(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    kode = query.data.split("_")[1]
    context.user_data["kode"] = kode

    keyboard = [
        [InlineKeyboardButton("⚖️ Timbang", callback_data="aksi_timbang")],
        [InlineKeyboardButton("🧼 Proses", callback_data="aksi_proses")],
        [InlineKeyboardButton("🚀 Antar", callback_data="aksi_antar")],
        [InlineKeyboardButton("✅ Selesai", callback_data="aksi_selesai")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="kembali")]
    ]

    query.message.reply_text(
        f"📦 Order: {kode}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
