import logging
import sqlite3
import random
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# ==============================
# CONFIG
# ==============================

TOKEN = "8729351085:AAEa2yXbwnCGccagbAZqSpV7LkIc12KJ_7E"
ADMIN_ID = 8028474070

logging.basicConfig(level=logging.INFO)

# ==============================
# DATABASE
# ==============================

conn = sqlite3.connect("laundry.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
id INTEGER PRIMARY KEY AUTOINCREMENT,
kode TEXT,
user_id INTEGER,
nama TEXT,
layanan TEXT,
alamat TEXT,
lat REAL,
lon REAL,
berat REAL,
harga INTEGER,
status TEXT,
tanggal TEXT
)
""")

conn.commit()

# ==============================
# UTIL
# ==============================

def generate_kode():
    return f"LDR-{random.randint(10000,99999)}"

# ==============================
# KEYBOARD
# ==============================

def user_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧺 Order Laundry", callback_data="order")],
        [InlineKeyboardButton("📦 Cek Status", callback_data="cek")]
    ])

def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["📊 Lihat Order"],
        ["🏠 Menu"]
    ], resize_keyboard=True)

# ==============================
# START
# ==============================

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Selamat datang di Bot Laundry",
        reply_markup=user_menu()
    )

# ==============================
# ADMIN COMMAND
# ==============================

def admin_command(update: Update, context: CallbackContext):

    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("❌ Bukan admin")
        return

    update.message.reply_text(
        "👑 ADMIN PANEL",
        reply_markup=admin_keyboard()
    )

# ==============================
# ORDER USER
# ==============================

def order(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("⚡ Express", callback_data="express")],
        [InlineKeyboardButton("🧼 Reguler", callback_data="reguler")],
        [InlineKeyboardButton("👕 Setrika", callback_data="setrika")]
    ]

    query.message.reply_text("Pilih layanan:", reply_markup=InlineKeyboardMarkup(keyboard))


def pilih_layanan(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    context.user_data["layanan"] = query.data

    location_button = KeyboardButton("📍 Kirim Lokasi", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True)

    query.message.reply_text("Kirim alamat atau lokasi:", reply_markup=keyboard)

# ==============================
# TERIMA LOKASI
# ==============================

def alamat_maps(update: Update, context: CallbackContext):

    if "layanan" not in context.user_data:
        return

    user = update.message.from_user
    layanan = context.user_data["layanan"]

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    kode = generate_kode()
    link_maps = f"https://maps.google.com/?q={lat},{lon}"

    cursor.execute("""
    INSERT INTO orders(kode,user_id,nama,layanan,lat,lon,status,tanggal)
    VALUES(?,?,?,?,?,?,?,?)
    """, (
        kode, user.id, user.first_name, layanan,
        lat, lon, "🚚 Menunggu dijemput",
        datetime.now().strftime("%d-%m-%Y")
    ))

    conn.commit()

    update.message.reply_text(f"""
✅ ORDER BERHASIL

Kode: {kode}
Layanan: {layanan}

📍 {link_maps}
""")

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

    # ==============================
    # INPUT ALAMAT USER
    # ==============================

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
