import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# HEALTH CHECK SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"PromptPilot Bot is running!"
        )

    def log_message(self, format, *args):
        return


def start_health_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    logger.info(
        f"Health server running on port {port}"
    )

    server.serve_forever()


# =========================================================
# USER LANGUAGE STORAGE
# =========================================================

user_languages = {}


# =========================================================
# TRANSLATIONS
# =========================================================

TEXTS = {

    "fa": {

        "language":
            "🌐 زبان خود را انتخاب کنید:",

        "welcome": (
            "🎉 خوش آمدید به PromptPilot!\n\n"
            "🤖 دستیار هوشمند ساخت Prompt\n\n"
            "ایده ساده خود را بنویسید و آن را "
            "به یک Prompt حرفه‌ای انگلیسی تبدیل کنید.\n\n"
            "👇 یکی از قابلیت‌ها را انتخاب کنید:"
        ),

        "generator":
            "🧠 تولید Prompt",

        "improver":
            "🔥 بهبود Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 تشخیص AI",

        "image":
            "🖼️ پرامپت تصویر",

        "video":
            "🎬 پرامپت ویدیو",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 بازسازی Prompt",

    },


    "en": {

        "language":
            "🌐 Choose your language:",

        "welcome": (
            "🎉 Welcome to PromptPilot!\n\n"
            "🤖 Your AI Prompt Assistant\n\n"
            "Turn your simple ideas into "
            "professional English prompts.\n\n"
            "👇 Choose a feature:"
        ),

        "generator":
            "🧠 Prompt Generator",

        "improver":
            "🔥 Prompt Improver",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 AI Detector",

        "image":
            "🖼️ Image Prompt",

        "video":
            "🎬 Video Prompt",

        "persian":
            "🌍 Persian → Pro Prompt",

        "remix":
            "🔄 Prompt Remix",

    },


    "ar": {

        "language":
            "🌐 اختر لغتك:",

        "welcome": (
            "🎉 أهلاً بك في PromptPilot!\n\n"
            "🤖 مساعدك الذكي لصناعة Prompts\n\n"
            "حوّل أفكارك البسيطة إلى "
            "Prompts احترافية باللغة الإنجليزية.\n\n"
            "👇 اختر إحدى الميزات:"
        ),

        "generator":
            "🧠 إنشاء Prompt",

        "improver":
            "🔥 تحسين Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 كاشف AI",

        "image":
            "🖼️ Prompt للصور",

        "video":
            "🎬 Prompt للفيديو",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 إعادة صياغة Prompt",

    }

}


# =========================================================
# LANGUAGE KEYBOARD
# =========================================================

def language_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "🇦🇫 فارسی",
                callback_data="lang_fa"
            )
        ],

        [
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_en"
            )
        ],

        [
            InlineKeyboardButton(
                "🇸🇦 العربية",
                callback_data="lang_ar"
            )
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# MAIN MENU
# =========================================================

def main_menu(lang):

    t = TEXTS[lang]

    keyboard = [

        [
            InlineKeyboardButton(
                t["generator"],
                callback_data="feature_generator"
            )
        ],

        [
            InlineKeyboardButton(
                t["improver"],
                callback_data="feature_improver"
            )
        ],

        [
            InlineKeyboardButton(
                t["doctor"],
                callback_data="feature_doctor"
            )
        ],

        [
            InlineKeyboardButton(
                t["detector"],
                callback_data="feature_detector"
            )
        ],

        [
            InlineKeyboardButton(
                t["image"],
                callback_data="feature_image"
            )
        ],

        [
            InlineKeyboardButton(
                t["video"],
                callback_data="feature_video"
            )
        ],

        [
            InlineKeyboardButton(
                t["persian"],
                callback_data="feature_persian"
            )
        ],

        [
            InlineKeyboardButton(
                t["remix"],
                callback_data="feature_remix"
            )
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if user_id in user_languages:

        lang = user_languages[user_id]

        await update.message.reply_text(
            TEXTS[lang]["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    await update.message.reply_text(
        "🌐 Choose your language / "
        "زبان خود را انتخاب کنید / "
        "اختر لغتك:",
        reply_markup=language_keyboard()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    data = query.data

    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    if data.startswith("lang_"):

        lang = data.replace(
            "lang_",
            ""
        )

        user_languages[user_id] = lang

        await query.edit_message_text(
            TEXTS[lang]["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    # -----------------------------------------------------
    # FEATURES
    # -----------------------------------------------------

    if data.startswith("feature_"):

        await query.answer(
            "Coming soon 🚀"
        )

        return


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    # Start HTTP server for Render
    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

    # Telegram application
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    print(
        "PromptPilot Bot is running..."
    )

    application.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
