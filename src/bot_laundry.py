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

TOKEN = "ISI_PAKE_TOKEN_BOT"
ADMIN_ID = 8028474070
