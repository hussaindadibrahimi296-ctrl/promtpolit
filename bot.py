import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from google import genai

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
# RENDER HEALTH SERVER
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

    "fa": {

        "language":
            "🌐 زبان خود را انتخاب کنید:",

        "welcome": (
            "🎉 خوش آمدید به PromptPilot!\n\n"
            "🤖 دستیار هوشمند ساخت Prompt\n\n"
            "ایده ساده خود را ارسال کنید و آن را "
            "به یک Prompt حرفه‌ای انگلیسی تبدیل کنید.\n\n"
            "👇 یکی از قابلیت‌ها را انتخاب کنید:"
        ),

        "generator":
            "🧠 AI Prompt Generator",

        "improver":
            "🔥 بهبود Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 تشخیص AI",

        "image":
            "🖼️ Image Prompt",

        "video":
            "🎬 Video Prompt",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 Prompt Remix",

        "generator_title":
            "🧠 AI Prompt Generator",

        "generator_help": (
            "🧠 AI Prompt Generator\n\n"
            "Prompt خود را برای چه کاری می‌خواهید؟\n\n"
            "👇 یکی را انتخاب کنید:"
        ),

        "chat":
            "💬 ChatGPT / AI",

        "logo":
            "🎨 Logo / Design",

        "social":
            "📱 Social Media",

        "writing":
            "✍️ Writing",

        "other":
            "🔧 Other",

        "send_idea": (
            "✍️ حالا ایده یا درخواست خود را به زبان خودتان "
            "ارسال کنید.\n\n"
            "من آن را به یک Prompt حرفه‌ای و کاملاً "
            "انگلیسی تبدیل می‌کنم."
        ),

        "image_help": (
            "🖼️ Image Prompt\n\n"
            "ایده تصویر خود را به زبان خودتان بنویسید.\n\n"
            "مثال:\n"
            "یک جنگجوی سامورایی در توکیو هنگام شب، "
            "نور سینمایی و فضای بارانی\n\n"
            "من آن را به یک Prompt حرفه‌ای برای "
            "تولید تصویر تبدیل می‌کنم.\n\n"
            "✍️ ایده تصویر را ارسال کنید:"
        ),

        "video_help": (
            "🎬 Video Prompt\n\n"
            "ایده ویدیوی خود را به زبان خودتان بنویسید.\n\n"
            "مثال:\n"
            "یک ماشین اسپرت قرمز در خیابان‌های دبی "
            "در شب، حرکت دوربین از جلو\n\n"
            "من آن را به یک Prompt حرفه‌ای برای "
            "تولید ویدیو تبدیل می‌کنم.\n\n"
            "✍️ ایده ویدیو را ارسال کنید:"
        ),

        "generating":
            "🧠 در حال ساخت Prompt حرفه‌ای...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error":
            "❌ در ساخت Prompt مشکلی پیش آمد.\n\n"
            "لطفاً دوباره تلاش کنید.",

        "home":
            "🏠 منوی اصلی",

        "improve":
            "🔥 بهبود",

        "remix_button":
            "🔄 Remix",

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
            "🧠 AI Prompt Generator",

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

        "generator_title":
            "🧠 AI Prompt Generator",

        "generator_help": (
            "🧠 AI Prompt Generator\n\n"
            "What do you want to create a prompt for?\n\n"
            "👇 Choose one:"
        ),

        "chat":
            "💬 ChatGPT / AI",

        "logo":
            "🎨 Logo / Design",

        "social":
            "📱 Social Media",

        "writing":
            "✍️ Writing",

        "other":
            "🔧 Other",

        "send_idea": (
            "✍️ Now send your idea or request in "
            "any language.\n\n"
            "I will transform it into a professional "
            "English prompt."
        ),

        "image_help": (
            "🖼️ Image Prompt\n\n"
            "Describe your image idea in any language.\n\n"
            "Example:\n"
            "A samurai warrior in Tokyo at night, "
            "cinematic lighting and rainy atmosphere.\n\n"
            "I will transform it into a professional "
            "image-generation prompt.\n\n"
            "✍️ Send your image idea:"
        ),

        "video_help": (
            "🎬 Video Prompt\n\n"
            "Describe your video idea in any language.\n\n"
            "Example:\n"
            "A red sports car driving through Dubai "
            "at night, camera moving from the front.\n\n"
            "I will transform it into a professional "
            "video-generation prompt.\n\n"
            "✍️ Send your video idea:"
        ),

        "generating":
            "🧠 Creating your professional prompt...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error":
            "❌ Something went wrong while creating "
            "your prompt.\n\n"
            "Please try again.",

        "home":
            "🏠 Main Menu",

        "improve":
            "🔥 Improve",

        "remix_button":
            "🔄 Remix",

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
            "🧠 AI Prompt Generator",

        "improver":
            "🔥 تحسين Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 كاشف AI",

        "image":
            "🖼️ Image Prompt",

        "video":
            "🎬 Video Prompt",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 إعادة صياغة Prompt",

        "generator_title":
            "🧠 AI Prompt Generator",

        "generator_help": (
            "🧠 AI Prompt Generator\n\n"
            "لأي شيء تريد إنشاء Prompt؟\n\n"
            "👇 اختر نوع Prompt:"
        ),

        "chat":
            "💬 ChatGPT / AI",

        "logo":
            "🎨 Logo / Design",

        "social":
            "📱 Social Media",

        "writing":
            "✍️ Writing",

        "other":
            "🔧 Other",

        "send_idea": (
            "✍️ أرسل فكرتك أو طلبك بأي لغة.\n\n"
            "سأحوّلها إلى Prompt احترافي باللغة الإنجليزية."
        ),

        "image_help": (
            "🖼️ Image Prompt\n\n"
            "اكتب فكرة الصورة بأي لغة.\n\n"
            "مثال:\n"
            "محارب ساموراي في طوكيو ليلاً، "
            "إضاءة سينمائية وأجواء ممطرة.\n\n"
            "سأحوّلها إلى Prompt احترافي لتوليد الصور.\n\n"
            "✍️ أرسل فكرة الصورة:"
        ),

        "video_help": (
            "🎬 Video Prompt\n\n"
            "اكتب فكرة الفيديو بأي لغة.\n\n"
            "مثال:\n"
            "سيارة رياضية حمراء في شوارع دبي ليلاً، "
            "والكاميرا تتحرك من الأمام.\n\n"
            "سأحوّلها إلى Prompt احترافي لتوليد الفيديو.\n\n"
            "✍️ أرسل فكرة الفيديو:"
        ),

        "generating":
            "🧠 جارٍ إنشاء Prompt احترافي...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error":
            "❌ حدث خطأ أثناء إنشاء Prompt.\n\n"
            "حاول مرة أخرى.",

        "home":
            "🏠 القائمة الرئيسية",

        "improve":
            "🔥 تحسين",

        "remix_button":
            "🔄 Remix",

    }

}


# =========================================================
# LANGUAGE KEYBOARD
# =========================================================

def language_keyboard():

    return InlineKeyboardMarkup([

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

    ])


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
# GENERATOR TYPE MENU
# =========================================================

def generator_type_keyboard(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                t["chat"],
                callback_data="type_chat"
            )
        ],

        [
            InlineKeyboardButton(
                t["image"],
                callback_data="type_image"
            )
        ],

        [
            InlineKeyboardButton(
                t["video"],
                callback_data="type_video"
            )
        ],

        [
            InlineKeyboardButton(
                t["logo"],
                callback_data="type_logo"
            )
        ],

        [
            InlineKeyboardButton(
                t["social"],
                callback_data="type_social"
            )
        ],

        [
            InlineKeyboardButton(
                t["writing"],
                callback_data="type_writing"
            )
        ],

        [
            InlineKeyboardButton(
                t["other"],
                callback_data="type_other"
            )
        ],

        [
            InlineKeyboardButton(
                t["home"],
                callback_data="home"
            )
        ],

    ])


# =========================================================
# RESULT KEYBOARD
# =========================================================

def result_keyboard(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([

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

    ])


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

    if user_id in user_languages:

        lang = user_languages[user_id]

        await update.message.reply_text(
            TEXTS[lang]["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    await update.message.reply_text(
        TEXTS["en"]["language"],
        reply_markup=language_keyboard()
    )


# =========================================================
# GEMINI PROMPT
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

    state = user_states.get(
        user_id,
        {}
    )

    idea = update.message.text.strip()

    if not idea:
        return

    if not gemini_client:

        logger.error(
            "GEMINI_API_KEY is missing."
        )

        await update.message.reply_text(
            TEXTS[lang]["error"]
        )

        return

    prompt_type = state.get(
        "prompt_type",
        "general"
    )

    if prompt_type == "image":

        instruction = """
Create a professional English prompt for an AI image generator.

Include appropriate visual details such as:
subject, environment, composition, lighting,
camera perspective, atmosphere, style, colors,
materials and important visual details.

Do not add unnecessary elements.
Output ONLY the final English prompt.
"""

    elif prompt_type == "video":

        instruction = """
Create a professional English prompt for an AI video generator.

Include appropriate details such as:
subject, environment, action, movement,
camera movement, camera perspective, lighting,
atmosphere, cinematic style, pacing and visual details.

Do not add unnecessary elements.
Output ONLY the final English prompt.
"""

    elif prompt_type == "chat":

        instruction = """
Create a professional English prompt for ChatGPT or another AI assistant.

Clearly define the role, objective, context,
requirements, constraints and desired output.

Output ONLY the final English prompt.
"""

    elif prompt_type == "logo":

        instruction = """
Create a professional English prompt for an AI logo/design generator.

Include the brand concept, visual identity,
style, composition, typography if relevant,
colors, symbolism and design direction.

Output ONLY the final English prompt.
"""

    elif prompt_type == "social":

        instruction = """
Create a professional English prompt for generating
high-quality social media content.

Include platform-appropriate content direction,
audience, tone, structure, hook and desired result.

Output ONLY the final English prompt.
"""

    elif prompt_type == "writing":

        instruction = """
Create a professional English writing prompt.

Clearly define the writing role, topic,
audience, tone, structure, requirements
and desired outcome.

Output ONLY the final English prompt.
"""

    else:

        instruction = """
Create a professional English prompt based on the user's idea.

Understand the user's intention and create a useful,
clear and detailed prompt.

Output ONLY the final English prompt.
"""

    full_prompt = f"""
You are PromptPilot, a professional AI prompt engineer.

{instruction}

Rules:

1. Understand the user's intention.
2. Do not translate literally.
3. Improve clarity and usefulness.
4. Do not invent unnecessary requirements.
5. The final result MUST be in English.
6. Do not explain your work.
7. Do not add "Prompt:".
8. Do not use markdown code fences.

User idea:

{idea}
"""

    await update.message.reply_text(
        TEXTS[lang]["generating"]
    )

    try:

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )

        result = response.text.strip()

        if not result:
            raise ValueError(
                "Empty Gemini response"
            )

        user_states[user_id]["last_prompt"] = result

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

    lang = user_languages.get(
        user_id,
        "en"
    )

    t = TEXTS[lang]

    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    if data.startswith("lang_"):

        selected_lang = data.replace(
            "lang_",
            ""
        )

        user_languages[user_id] = selected_lang

        user_states.pop(
            user_id,
            None
        )

        await query.edit_message_text(
            TEXTS[selected_lang]["welcome"],
            reply_markup=main_menu(selected_lang)
        )

        return

    # -----------------------------------------------------
    # GENERAL PROMPT GENERATOR
    # -----------------------------------------------------

    if data == "feature_generator":

        user_states[user_id] = {
            "mode": "generator"
        }

        await query.edit_message_text(
            t["generator_help"],
            reply_markup=generator_type_keyboard(lang)
        )

        return

    # -----------------------------------------------------
    # IMAGE PROMPT
    # -----------------------------------------------------

    if data == "feature_image":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "image"
        }

        await query.edit_message_text(
            t["image_help"],
            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        t["home"],
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    # -----------------------------------------------------
    # VIDEO PROMPT
    # -----------------------------------------------------

    if data == "feature_video":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "video"
        }

        await query.edit_message_text(
            t["video_help"],
            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        t["home"],
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    # -----------------------------------------------------
    # GENERATOR TYPES
    # -----------------------------------------------------

    if data.startswith("type_"):

        selected_type = data.replace(
            "type_",
            ""
        )

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": selected_type
        }

        await query.edit_message_text(
            t["send_idea"],
            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        t["home"],
                        callback_data="home"
                    )
                ]

            ])
        )

        return

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if data == "home":

        user_states.pop(
            user_id,
            None
        )

        await query.edit_message_text(
            t["welcome"],
            reply_markup=main_menu(lang)
        )

        return

    # -----------------------------------------------------
    # FUTURE FEATURES
    # -----------------------------------------------------

    if data.startswith("feature_"):

        await query.answer(
            "Coming soon 🚀"
        )

        return

    # -----------------------------------------------------
    # FUTURE ACTIONS
    # -----------------------------------------------------

    if data.startswith("action_"):

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

    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

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
