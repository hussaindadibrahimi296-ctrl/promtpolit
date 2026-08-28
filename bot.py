import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from google import genai

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# GEMINI
# =========================================================

gemini_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# =========================================================
# HEALTH SERVER
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
# USER DATA
# =========================================================

user_languages = {}

user_states = {}


# =========================================================
# TRANSLATIONS
# =========================================================

TEXTS = {

    # =====================================================
    # FARSI
    # =====================================================

    "fa": {

        "language":
            "🌐 زبان خود را انتخاب کنید:",

        "welcome": (
            "🤖 PromptPilot\n\n"
            "👋 خوش آمدید!\n\n"
            "PromptPilot به شما کمک می‌کند ایده‌های ساده "
            "خود را به Promptهای حرفه‌ای برای ابزارهای AI "
            "تبدیل کنید.\n\n"
            "👇 یک قابلیت را انتخاب کنید:"
        ),

        "generator":
            "🧠 تولید Prompt",

        "improver":
            "🔥 بهبود Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 AI Detector",

        "image":
            "🖼️ Image Prompt",

        "video":
            "🎬 Video Prompt",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 Prompt Remix",

        "generator_help": (
            "🧠 تولید Prompt\n\n"
            "ایده خود را به هر زبانی که می‌خواهید "
            "برای من ارسال کنید.\n\n"
            "مثال:\n"
            "یک ماشین لوکس در یک شهر مدرن در شب\n\n"
            "من ایده شما را به یک Prompt حرفه‌ای "
            "و دقیق به زبان انگلیسی تبدیل می‌کنم.\n\n"
            "✍️ حالا ایده خود را ارسال کنید:"
        ),

        "generating":
            "🧠 در حال ساخت Prompt حرفه‌ای...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error": (
            "❌ متأسفانه در ساخت Prompt مشکلی پیش آمد.\n\n"
            "لطفاً دوباره تلاش کنید."
        ),

        "copy":
            "📋 کپی",

        "improve":
            "🔥 بهبود",

        "remix_button":
            "🔄 Remix",

        "home":
            "🏠 منوی اصلی",

        "coming_soon":
            "این قابلیت به‌زودی فعال می‌شود 🚀",
    },


    # =====================================================
    # ENGLISH
    # =====================================================

    "en": {

        "language":
            "🌐 Choose your language:",

        "welcome": (
            "🤖 PromptPilot\n\n"
            "👋 Welcome!\n\n"
            "PromptPilot helps you turn simple ideas "
            "into professional prompts for AI tools.\n\n"
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

        "generator_help": (
            "🧠 Prompt Generator\n\n"
            "Send me your idea in any language.\n\n"
            "Example:\n"
            "A luxury car in a modern city at night\n\n"
            "I will transform your idea into a "
            "professional and detailed English prompt.\n\n"
            "✍️ Now send your idea:"
        ),

        "generating":
            "🧠 Creating your professional prompt...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error": (
            "❌ Something went wrong while creating "
            "your prompt.\n\n"
            "Please try again."
        ),

        "copy":
            "📋 Copy",

        "improve":
            "🔥 Improve",

        "remix_button":
            "🔄 Remix",

        "home":
            "🏠 Main Menu",

        "coming_soon":
            "This feature is coming soon 🚀",
    },


    # =====================================================
    # ARABIC
    # =====================================================

    "ar": {

        "language":
            "🌐 اختر لغتك:",

        "welcome": (
            "🤖 PromptPilot\n\n"
            "👋 أهلاً بك!\n\n"
            "يساعدك PromptPilot على تحويل أفكارك البسيطة "
            "إلى Prompts احترافية لأدوات الذكاء الاصطناعي.\n\n"
            "👇 اختر إحدى الميزات:"
        ),

        "generator":
            "🧠 إنشاء Prompt",

        "improver":
            "🔥 تحسين Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 AI Detector",

        "image":
            "🖼️ Image Prompt",

        "video":
            "🎬 Video Prompt",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 Prompt Remix",

        "generator_help": (
            "🧠 إنشاء Prompt\n\n"
            "أرسل فكرتك بأي لغة تريدها.\n\n"
            "مثال:\n"
            "سيارة فاخرة في مدينة حديثة ليلاً\n\n"
            "سأحوّل فكرتك إلى Prompt احترافي "
            "ودقيق باللغة الإنجليزية.\n\n"
            "✍️ أرسل فكرتك الآن:"
        ),

        "generating":
            "🧠 جارٍ إنشاء Prompt احترافي...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error": (
            "❌ حدث خطأ أثناء إنشاء Prompt.\n\n"
            "حاول مرة أخرى."
        ),

        "copy":
            "📋 نسخ",

        "improve":
            "🔥 تحسين",

        "remix_button":
            "🔄 Remix",

        "home":
            "🏠 القائمة الرئيسية",

        "coming_soon":
            "هذه الميزة ستكون متاحة قريباً 🚀",
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

    return InlineKeyboardMarkup(keyboard)


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

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# RESULT KEYBOARD
# =========================================================

def result_keyboard(lang):

    t = TEXTS[lang]

    keyboard = [

        [
            InlineKeyboardButton(
                t["improve"],
                callback_data="action_improve"
            ),

            InlineKeyboardButton(
                t["remix_button"],
                callback_data="action_remix"
            ),
        ],

        [
            InlineKeyboardButton(
                t["home"],
                callback_data="home"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    user_states.pop(
        user_id,
        None
    )

    # -----------------------------------------------------
    # User already selected a language
    # -----------------------------------------------------

    if user_id in user_languages:

        lang = user_languages[user_id]

        await update.message.reply_text(
            TEXTS[lang]["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    # -----------------------------------------------------
    # New user
    # -----------------------------------------------------

    await update.message.reply_text(
        "🌐 Choose your language / "
        "زبان خود را انتخاب کنید / "
        "اختر لغتك:",
        reply_markup=language_keyboard()
    )


# =========================================================
# GENERATE PROMPT
# =========================================================

async def generate_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    lang = user_languages.get(
        user_id,
        "en"
    )

    # -----------------------------------------------------
    # Only Generator mode should process messages
    # -----------------------------------------------------

    state = user_states.get(
        user_id,
        {}
    )

    if state.get("mode") != "generator":

        return

    idea = update.message.text.strip()

    if not idea:

        return

    if not gemini_client:

        await update.message.reply_text(
            TEXTS[lang]["error"]
        )

        logger.error(
            "GEMINI_API_KEY is missing."
        )

        return

    await update.message.reply_text(
        TEXTS[lang]["generating"]
    )

    try:

        prompt = f"""
You are PromptPilot, a professional AI prompt engineer.

The user will provide an idea in any language.

Your task is to transform the user's idea into
one highly professional, detailed, useful English prompt.

Rules:

1. Output ONLY the final English prompt.
2. Never explain your changes.
3. Never translate literally.
4. Understand the user's actual intention.
5. Add useful context and details when appropriate.
6. Keep the result natural and practical.
7. Do not invent unnecessary requirements.
8. The final answer must be in English.
9. Do not use markdown code fences.
10. Do not add labels such as "Prompt:".

User idea:

{idea}
"""

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        result = response.text.strip()

        if not result:

            raise ValueError(
                "Gemini returned an empty response."
            )

        user_states[user_id] = {
            "mode": "generator",
            "last_prompt": result
        }

        await update.message.reply_text(
            TEXTS[lang]["result"] + result,
            reply_markup=result_keyboard(lang)
        )

    except Exception as e:

        logger.error(
            "Gemini error: %s",
            e,
            exc_info=True
        )

        await update.message.reply_text(
            TEXTS[lang]["error"]
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

    # =====================================================
    # LANGUAGE
    # =====================================================

    if data.startswith("lang_"):

        lang = data.replace(
            "lang_",
            ""
        )

        if lang not in TEXTS:

            return

        user_languages[user_id] = lang

        user_states.pop(
            user_id,
            None
        )

        await query.edit_message_text(
            TEXTS[lang]["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    # =====================================================
    # GENERATOR
    # =====================================================

    if data == "feature_generator":

        lang = user_languages.get(
            user_id,
            "en"
        )

        user_states[user_id] = {
            "mode": "generator"
        }

        await query.edit_message_text(
            TEXTS[lang]["generator_help"],
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        TEXTS[lang]["home"],
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        lang = user_languages.get(
            user_id,
            "en"
        )

        user_states.pop(
            user_id,
            None
        )

        await query.edit_message_text(
            TEXTS[lang]["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    # =====================================================
    # FUTURE FEATURES
    # =====================================================

    if data.startswith("feature_"):

        lang = user_languages.get(
            user_id,
            "en"
        )

        await query.answer(
            TEXTS[lang]["coming_soon"]
        )

        return

    # =====================================================
    # FUTURE ACTIONS
    # =====================================================

    if data.startswith("action_"):

        lang = user_languages.get(
            user_id,
            "en"
        )

        await query.answer(
            TEXTS[lang]["coming_soon"]
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

    # -----------------------------------------------------
    # Start Render health server
    # -----------------------------------------------------

    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

    # -----------------------------------------------------
    # Telegram application
    # -----------------------------------------------------

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

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            generate_prompt
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
