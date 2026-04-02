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

TOKEN = "ISI_TOKEN_LO"
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
# START
# ==============================

def start(update: Update, context: CallbackContext):

    keyboard = [
        [InlineKeyboardButton("🧺 Order Laundry", callback_data="order")],
        [InlineKeyboardButton("📦 Cek Status", callback_data="cek")]
    ]

    update.message.reply_text(
        "Selamat datang di Bot Laundry",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==============================
# ADMIN COMMAND
# ==============================

def admin_command(update: Update, context: CallbackContext):

    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("❌ Kamu bukan admin")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Lihat Order", callback_data="lihat")]
    ]

    update.message.reply_text(
        "👑 Menu Admin",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==============================
# ORDER USER
# ==============================

def order(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

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

    query.message.reply_text(
        "Kirim alamat atau lokasi:",
        reply_markup=keyboard
    )

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

    # INPUT ALAMAT MANUAL
    if "layanan" in context.user_data:

        layanan = context.user_data["layanan"]
        kode = generate_kode()

        cursor.execute("""
        INSERT INTO orders(kode,user_id,nama,layanan,alamat,status,tanggal)
        VALUES(?,?,?,?,?,?,?)
        """, (
            kode, user.id, user.first_name, layanan,
            text, "🚚 Menunggu dijemput",
            datetime.now().strftime("%d-%m-%Y")
        ))

        conn.commit()

        update.message.reply_text(f"""
✅ ORDER BERHASIL

Kode: {kode}
Alamat: {text}
""")

        context.bot.send_message(ADMIN_ID, f"""
🔔 ORDER BARU

Kode: {kode}
Nama: {user.first_name}
Alamat: {text}
""")

        context.user_data.clear()
        return

    # INPUT BERAT (ADMIN)
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

        update.message.reply_text("✅ Berhasil ditimbang")

        context.user_data.clear()

# ==============================
# ADMIN FLOW (BUTTON BASED)
# ==============================

def lihat_order(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    cursor.execute("SELECT kode,nama FROM orders ORDER BY id DESC LIMIT 10")
    data = cursor.fetchall()

    if not data:
        query.message.reply_text("Belum ada order")
        return

    keyboard = [
        [InlineKeyboardButton(f"{d[0]} - {d[1]}", callback_data=f"detail_{d[0]}")]
        for d in data
    ]

    query.message.reply_text("📊 Pilih Order:", reply_markup=InlineKeyboardMarkup(keyboard))


def detail_order(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    kode = query.data.split("_")[1]

    cursor.execute("SELECT nama,layanan,status FROM orders WHERE kode=?", (kode,))
    data = cursor.fetchone()

    if not data:
        query.message.reply_text("Data tidak ditemukan")
        return

    nama, layanan, status = data

    keyboard = [
        [InlineKeyboardButton("⚖️ Timbang", callback_data=f"timbang_{kode}")],
        [InlineKeyboardButton("🧼 Proses", callback_data=f"proses_{kode}")],
        [InlineKeyboardButton("🚀 Antar", callback_data=f"antar_{kode}")],
        [InlineKeyboardButton("✅ Selesai", callback_data=f"selesai_{kode}")]
    ]

    query.message.reply_text(f"""
📦 DETAIL ORDER

Kode: {kode}
Nama: {nama}
Layanan: {layanan}
Status: {status}
""", reply_markup=InlineKeyboardMarkup(keyboard))


def tombol_timbang(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    kode = query.data.split("_")[1]

    context.user_data["kode"] = kode
    context.user_data["berat"] = True

    query.message.reply_text(f"Masukkan berat untuk {kode}")


def tombol_status(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    aksi, kode = query.data.split("_")

    status_map = {
        "proses": "🧼 Diproses",
        "antar": "🚀 Diantar",
        "selesai": "✅ Selesai"
    }

    status = status_map[aksi]

    cursor.execute("SELECT user_id FROM orders WHERE kode=?", (kode,))
    user_id = cursor.fetchone()[0]

    cursor.execute("UPDATE orders SET status=? WHERE kode=?", (status, kode))
    conn.commit()

    context.bot.send_message(user_id, f"""
📦 UPDATE LAUNDRY

Kode: {kode}
Status: {status}
""")

    query.message.reply_text("✅ Status berhasil diupdate")

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

    dp.add_handler(CallbackQueryHandler(lihat_order, pattern="lihat"))
    dp.add_handler(CallbackQueryHandler(detail_order, pattern="detail_"))
    dp.add_handler(CallbackQueryHandler(tombol_timbang, pattern="timbang_"))
    dp.add_handler(CallbackQueryHandler(tombol_status, pattern="proses_|antar_|selesai_"))

    dp.add_handler(MessageHandler(Filters.location, alamat_maps))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()