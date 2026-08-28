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

    # =====================================================
    # FARSI
    # =====================================================

    "fa": {

        "language":
            "🌐 زبان خود را انتخاب کنید:",

        "welcome": (
            "🎉 خوش آمدید به PromptPilot!\n\n"
            "🤖 دستیار هوشمند ساخت Prompt\n\n"
            "ایده ساده خود را ارسال کنید و آن را "
            "به یک Prompt حرفه‌ای انگلیسی تبدیل کنید.\n\n"
            "💡 هرچه ایده و جزئیات بیشتری بدهید، "
            "Prompt نهایی دقیق‌تر و حرفه‌ای‌تر خواهد بود.\n\n"
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
            "🖼️ Prompt تصویر",

        "video":
            "🎬 Prompt ویدیو",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 بازسازی Prompt",

        "generator_title":
            "🧠 تولید Prompt",

        "generator_help": (
            "🧠 تولید Prompt\n\n"
            "این بخش برای ساخت Promptهای حرفه‌ای "
            "برای کارهای مختلف است.\n\n"
            "ابتدا نوع کاری را انتخاب کنید، سپس "
            "ایده خود را با جزئیات برای من بفرستید.\n\n"
            "💡 نکته مهم:\n"
            "اگر ایده خود را دقیق‌تر توضیح دهید، "
            "Prompt حرفه‌ای‌تر و کاربردی‌تری دریافت می‌کنید.\n\n"
            "مثال ضعیف:\n"
            "❌ یک لوگو بساز\n\n"
            "مثال قوی:\n"
            "✅ Create a modern minimalist logo for a "
            "technology brand called Nova, using a clean "
            "geometric symbol and a premium professional style.\n\n"
            "👇 نوع Prompt را انتخاب کنید:"
        ),

        "logo":
            "🎨 Logo / Design",

        "social":
            "📱 Social Media",

        "writing":
            "✍️ Writing",

        "other":
            "🔧 Other",

        "send_idea_general": (
            "✍️ حالا ایده خود را با جزئیات ارسال کنید.\n\n"
            "💡 برای نتیجه بهتر این موارد را تا حد امکان "
            "توضیح دهید:\n"
            "• هدف شما چیست؟\n"
            "• موضوع دقیق چیست؟\n"
            "• سبک موردنظر چیست؟\n"
            "• برای چه کسی یا چه پلتفرمی است؟\n"
            "• محدودیت یا ویژگی خاصی دارید؟\n\n"
            "❌ ایده ضعیف:\n"
            "«یک پست بساز»\n\n"
            "✅ ایده قوی:\n"
            "«برای اینستاگرام یک پست معرفی محصول جدید "
            "برای جوانان بساز، لحن دوستانه و حرفه‌ای باشد "
            "و یک Hook جذاب در ابتدای متن داشته باشد.»\n\n"
            "🚀 هرچه توضیحات بیشتر باشد، Prompt حرفه‌ای‌تر می‌شود.\n\n"
            "👇 ایده خود را بفرستید:"
        ),

        "image_help": (
            "🖼️ Prompt تصویر\n\n"
            "این قابلیت مخصوص ساخت Prompt حرفه‌ای برای "
            "تولید تصاویر با هوش مصنوعی است.\n\n"
            "من روی جزئیات تصویری مانند سوژه، محیط، "
            "نورپردازی، ترکیب‌بندی، زاویه دوربین، "
            "رنگ، سبک و فضای تصویر تمرکز می‌کنم.\n\n"
            "❌ ایده ضعیف:\n"
            "«یک ماشین زیبا»\n\n"
            "✅ ایده قوی:\n"
            "«یک خودروی اسپرت مشکی لوکس در خیابان‌های "
            "توکیو در شب، باران شدید، نورهای نئون، "
            "انعکاس نور روی آسفالت خیس، نمای سینمایی "
            "از زاویه پایین.»\n\n"
            "💡 هرچه جزئیات بیشتری درباره تصویر بدهید، "
            "Prompt دقیق‌تر می‌شود.\n\n"
            "✍️ ایده تصویر خود را ارسال کنید:"
        ),

        "video_help": (
            "🎬 Prompt ویدیو\n\n"
            "این قابلیت مخصوص ساخت Prompt حرفه‌ای برای "
            "تولید ویدیو با هوش مصنوعی است.\n\n"
            "من روی حرکت سوژه، حرکت دوربین، محیط، "
            "نورپردازی، زمان‌بندی، زاویه دوربین، "
            "فضا و سبک سینمایی تمرکز می‌کنم.\n\n"
            "❌ ایده ضعیف:\n"
            "«یک ماشین در شهر حرکت کند»\n\n"
            "✅ ایده قوی:\n"
            "«یک خودروی اسپرت قرمز در خیابان‌های دبی "
            "در شب حرکت می‌کند؛ دوربین از نمای جلویی "
            "به‌آرامی عقب می‌رود، نورهای شهر روی بدنه "
            "انعکاس دارند و صحنه با حرکت سینمایی نرم "
            "و عمق میدان کم فیلم‌برداری می‌شود.»\n\n"
            "💡 هرچه حرکت و فضای ویدیو را دقیق‌تر توضیح دهید، "
            "Prompt حرفه‌ای‌تر می‌شود.\n\n"
            "✍️ ایده ویدیوی خود را ارسال کنید:"
        ),

        "logo_help": (
            "🎨 Logo / Design\n\n"
            "این قابلیت برای ساخت Prompt حرفه‌ای جهت طراحی "
            "لوگو، هویت بصری و طرح‌های گرافیکی است.\n\n"
            "❌ ضعیف:\n"
            "«یک لوگوی خوب برای یک شرکت بساز»\n\n"
            "✅ قوی:\n"
            "«برای یک برند تکنولوژی به نام Nova یک لوگوی "
            "مینیمال و مدرن با نماد هندسی، ظاهر لوکس، "
            "قابل استفاده در اپلیکیشن و شبکه‌های اجتماعی طراحی کن.»\n\n"
            "💡 نام برند، حوزه فعالیت، سبک و رنگ موردنظر "
            "را توضیح دهید.\n\n"
            "✍️ ایده طراحی خود را ارسال کنید:"
        ),

        "social_help": (
            "📱 Social Media\n\n"
            "این قابلیت برای ساخت Prompt حرفه‌ای جهت "
            "تولید محتوای شبکه‌های اجتماعی است.\n\n"
            "❌ ضعیف:\n"
            "«برای اینستاگرام یک پست بساز»\n\n"
            "✅ قوی:\n"
            "«برای Instagram یک کپشن معرفی محصول جدید "
            "برای مخاطبان 18 تا 30 ساله بنویس، لحن "
            "دوستانه و حرفه‌ای باشد و با یک Hook قدرتمند شروع شود.»\n\n"
            "💡 پلتفرم، مخاطب، موضوع و لحن را توضیح دهید.\n\n"
            "✍️ ایده محتوای خود را ارسال کنید:"
        ),

        "writing_help": (
            "✍️ Writing\n\n"
            "این قابلیت برای ساخت Prompt حرفه‌ای جهت "
            "نوشتن مقاله، داستان، کپشن، ایمیل و انواع متن است.\n\n"
            "❌ ضعیف:\n"
            "«یک مقاله درباره هوش مصنوعی بنویس»\n\n"
            "✅ قوی:\n"
            "«یک مقاله آموزشی 1200 کلمه‌ای درباره تأثیر "
            "هوش مصنوعی بر تولید محتوا برای مبتدیان بنویس، "
            "با ساختار واضح، مثال‌های واقعی و لحن ساده.»\n\n"
            "💡 موضوع، مخاطب، طول، لحن و نتیجه موردنظر "
            "را توضیح دهید.\n\n"
            "✍️ ایده خود را ارسال کنید:"
        ),

        "other_help": (
            "🔧 Other\n\n"
            "برای هر نوع کاری که در دسته‌های دیگر قرار نمی‌گیرد "
            "می‌توانید از این بخش استفاده کنید.\n\n"
            "من هدف شما را بررسی می‌کنم و بر اساس آن "
            "یک Prompt حرفه‌ای انگلیسی می‌سازم.\n\n"
            "❌ ضعیف:\n"
            "«یک Prompt خوب بساز»\n\n"
            "✅ قوی:\n"
            "«می‌خواهم یک برنامه مطالعاتی برای یادگیری زبان "
            "انگلیسی در سه ماه داشته باشم. روزانه یک ساعت وقت دارم "
            "و سطح من متوسط است.»\n\n"
            "💡 هدف خود را تا حد ممکن کامل توضیح دهید.\n\n"
            "✍️ ایده خود را ارسال کنید:"
        ),

        "improve_help": (
            "🔥 بهبود Prompt\n\n"
            "یک Prompt موجود را برای من ارسال کنید.\n\n"
            "من آن را از نظر وضوح، ساختار، جزئیات و نتیجه "
            "نهایی بهبود می‌دهم.\n\n"
            "💡 اگر بگویید Prompt برای چه ابزار یا کاری استفاده "
            "می‌شود، نتیجه دقیق‌تر خواهد بود.\n\n"
            "✍️ Prompt خود را ارسال کنید:"
        ),

        "doctor_help": (
            "🩺 Prompt Doctor\n\n"
            "Prompt خود را ارسال کنید.\n\n"
            "من مشکلات آن را پیدا می‌کنم؛ مانند ابهام، "
            "دستور ناقص، ساختار ضعیف یا اطلاعات ناکافی.\n\n"
            "سپس نسخه بهتر آن را پیشنهاد می‌کنم.\n\n"
            "✍️ Prompt خود را ارسال کنید:"
        ),

        "detector_help": (
            "🎯 AI Detector\n\n"
            "متن خود را ارسال کنید تا آن را بررسی کنم و "
            "نشانه‌های احتمالی تولید توسط AI را تحلیل کنم.\n\n"
            "⚠️ این ابزار تشخیص قطعی و صددرصدی ارائه نمی‌کند؛ "
            "نتیجه یک تحلیل احتمالی است.\n\n"
            "✍️ متن خود را ارسال کنید:"
        ),

        "persian_help": (
            "🌍 فارسی → Pro Prompt\n\n"
            "ایده فارسی خود را ارسال کنید.\n\n"
            "من مفهوم اصلی را درک می‌کنم و به جای ترجمه "
            "کلمه‌به‌کلمه، آن را به یک Prompt حرفه‌ای انگلیسی "
            "تبدیل می‌کنم.\n\n"
            "❌ ضعیف:\n"
            "«یک عکس خوب از یک خانه بساز»\n\n"
            "✅ قوی:\n"
            "«یک خانه مدرن مینیمال در میان جنگل، هنگام طلوع "
            "آفتاب، با پنجره‌های بزرگ، نور طبیعی و سبک "
            "معماری لوکس طراحی کن.»\n\n"
            "✍️ ایده فارسی خود را ارسال کنید:"
        ),

        "remix_help": (
            "🔄 Prompt Remix\n\n"
            "Prompt خود را ارسال کنید.\n\n"
            "من همان مفهوم اصلی را حفظ می‌کنم اما آن را "
            "با ساختار و سبک متفاوت بازنویسی می‌کنم.\n\n"
            "💡 اگر سبک خاصی می‌خواهید، آن را هم ذکر کنید.\n\n"
            "✍️ Prompt خود را ارسال کنید:"
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

        "back":
            "🔙 بازگشت",

        "improve":
            "🔥 بهبود",

        "remix_button":
            "🔄 Remix",

    },


    # =====================================================
    # ENGLISH
    # =====================================================

    "en": {

        "language":
            "🌐 Choose your language:",

        "welcome": (
            "🎉 Welcome to PromptPilot!\n\n"
            "🤖 Your AI Prompt Assistant\n\n"
            "Turn your simple ideas into professional "
            "English prompts.\n\n"
            "💡 The more details you provide, the more "
            "accurate and professional your prompt will be.\n\n"
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

        "generator_title":
            "🧠 Prompt Generator",

        "generator_help": (
            "🧠 Prompt Generator\n\n"
            "Use this section to create professional "
            "prompts for different tasks.\n\n"
            "First choose the type of task, then describe "
            "your idea with as much detail as possible.\n\n"
            "💡 The more details you provide, the better "
            "your final prompt will be.\n\n"
            "Weak example:\n"
            "❌ Make a logo\n\n"
            "Strong example:\n"
            "✅ Create a modern minimalist logo for a "
            "technology brand called Nova, using a clean "
            "geometric symbol and a premium professional style.\n\n"
            "👇 Choose the prompt type:"
        ),

        "logo":
            "🎨 Logo / Design",

        "social":
            "📱 Social Media",

        "writing":
            "✍️ Writing",

        "other":
            "🔧 Other",

        "send_idea_general": (
            "✍️ Now send your idea with as much detail as possible.\n\n"
            "💡 For better results, include:\n"
            "• What is your goal?\n"
            "• What is the exact topic?\n"
            "• What style do you want?\n"
            "• Who is the audience?\n"
            "• Any requirements or limitations?\n\n"
            "❌ Weak idea:\n"
            "\"Create a post\"\n\n"
            "✅ Strong idea:\n"
            "\"Create an Instagram product-launch post "
            "for people aged 18–30. Use a friendly but "
            "professional tone and start with a strong hook.\"\n\n"
            "🚀 More details = a more professional prompt.\n\n"
            "👇 Send your idea:"
        ),

        "image_help": (
            "🖼️ Image Prompt\n\n"
            "This feature creates professional prompts for "
            "AI image-generation tools.\n\n"
            "I focus on visual details such as the subject, "
            "environment, lighting, composition, camera angle, "
            "colors, style and atmosphere.\n\n"
            "❌ Weak idea:\n"
            "\"A beautiful car\"\n\n"
            "✅ Strong idea:\n"
            "\"A luxurious black sports car on a rainy Tokyo "
            "street at night, neon lights, reflections on wet "
            "asphalt, cinematic low-angle composition.\"\n\n"
            "💡 The more visual details you provide, the better "
            "the prompt will be.\n\n"
            "✍️ Send your image idea:"
        ),

        "video_help": (
            "🎬 Video Prompt\n\n"
            "This feature creates professional prompts for "
            "AI video-generation tools.\n\n"
            "I focus on subject movement, camera movement, "
            "environment, lighting, timing, perspective, "
            "atmosphere and cinematic style.\n\n"
            "❌ Weak idea:\n"
            "\"A car driving in a city\"\n\n"
            "✅ Strong idea:\n"
            "\"A red sports car driving through Dubai at night; "
            "the camera slowly pulls backward from the front, "
            "city lights reflect across the body, with smooth "
            "cinematic motion and shallow depth of field.\"\n\n"
            "💡 Describe the movement and atmosphere in detail "
            "for a stronger prompt.\n\n"
            "✍️ Send your video idea:"
        ),

        "logo_help": (
            "🎨 Logo / Design\n\n"
            "Create professional prompts for logos, visual "
            "identity and graphic design.\n\n"
            "❌ Weak:\n"
            "\"Make a good logo for a company\"\n\n"
            "✅ Strong:\n"
            "\"Create a minimalist modern logo for a technology "
            "brand called Nova, using a geometric symbol, "
            "premium appearance and a design suitable for apps "
            "and social media.\"\n\n"
            "💡 Include the brand name, industry, style and colors.\n\n"
            "✍️ Send your design idea:"
        ),

        "social_help": (
            "📱 Social Media\n\n"
            "Create professional prompts for social-media content.\n\n"
            "❌ Weak:\n"
            "\"Make an Instagram post\"\n\n"
            "✅ Strong:\n"
            "\"Create an Instagram caption introducing a new "
            "product to users aged 18–30. Use a friendly "
            "professional tone and start with a strong hook.\"\n\n"
            "💡 Include the platform, audience, topic and tone.\n\n"
            "✍️ Send your content idea:"
        ),

        "writing_help": (
            "✍️ Writing\n\n"
            "Create professional prompts for articles, stories, "
            "captions, emails and other writing tasks.\n\n"
            "❌ Weak:\n"
            "\"Write an article about AI\"\n\n"
            "✅ Strong:\n"
            "\"Write a 1,200-word beginner-friendly educational "
            "article about how AI is changing content creation, "
            "using clear structure, real examples and simple language.\"\n\n"
            "💡 Include the topic, audience, length, tone and goal.\n\n"
            "✍️ Send your idea:"
        ),

        "other_help": (
            "🔧 Other\n\n"
            "Use this feature for tasks that do not fit the other categories.\n\n"
            "I will understand your goal and create a professional "
            "English prompt for it.\n\n"
            "❌ Weak:\n"
            "\"Make a good prompt\"\n\n"
            "✅ Strong:\n"
            "\"Create a three-month English study plan for an "
            "intermediate learner who can study one hour every day.\"\n\n"
            "💡 Explain your goal as clearly as possible.\n\n"
            "✍️ Send your idea:"
        ),

        "improve_help": (
            "🔥 Prompt Improver\n\n"
            "Send me an existing prompt.\n\n"
            "I will improve its clarity, structure, details and "
            "expected result.\n\n"
            "💡 Tell me what tool or task the prompt is for "
            "if possible.\n\n"
            "✍️ Send your prompt:"
        ),

        "doctor_help": (
            "🩺 Prompt Doctor\n\n"
            "Send me your prompt.\n\n"
            "I will identify problems such as unclear instructions, "
            "missing information, weak structure or unnecessary details.\n\n"
            "Then I will suggest an improved version.\n\n"
            "✍️ Send your prompt:"
        ),

        "detector_help": (
            "🎯 AI Detector\n\n"
            "Send your text and I will analyze signs that may "
            "indicate AI-generated writing.\n\n"
            "⚠️ This is not a 100% certain detector. "
            "The result is an analysis, not definitive proof.\n\n"
            "✍️ Send your text:"
        ),

        "persian_help": (
            "🌍 Persian → Pro Prompt\n\n"
            "Send your idea in Persian.\n\n"
            "I will understand the meaning and transform it into "
            "a professional English prompt instead of translating "
            "word by word.\n\n"
            "❌ Weak:\n"
            "\"Make a good picture of a house\"\n\n"
            "✅ Strong:\n"
            "\"Create a modern minimalist house in a forest at "
            "sunrise, featuring large windows, natural lighting "
            "and luxurious architecture.\"\n\n"
            "✍️ Send your Persian idea:"
        ),

        "remix_help": (
            "🔄 Prompt Remix\n\n"
            "Send your prompt.\n\n"
            "I will preserve the original concept while "
            "rewriting it with a different structure and style.\n\n"
            "💡 Mention your preferred style if you have one.\n\n"
            "✍️ Send your prompt:"
        ),

        "generating":
            "🧠 Creating your professional prompt...",

        "result":
            "✨ Professional English Prompt\n\n",

        "error":
            "❌ Something went wrong while creating your prompt.\n\n"
            "Please try again.",

        "home":
            "🏠 Main Menu",

        "back":
            "🔙 Back",

        "improve":
            "🔥 Improve",

        "remix_button":
            "🔄 Remix",

    },


    # =====================================================
    # ARABIC
    # =====================================================

    "ar": {

        "language":
            "🌐 اختر لغتك:",

        "welcome": (
            "🎉 أهلاً بك في PromptPilot!\n\n"
            "🤖 مساعدك الذكي لصناعة Prompts\n\n"
            "حوّل أفكارك البسيطة إلى Prompts احترافية "
            "باللغة الإنجليزية.\n\n"
            "💡 كلما شرحت فكرتك بتفاصيل أكثر، حصلت على "
            "Prompt أكثر دقة واحترافية.\n\n"
            "👇 اختر إحدى الميزات:"
        ),

        "generator":
            "🧠 مولد Prompt",

        "improver":
            "🔥 تحسين Prompt",

        "doctor":
            "🩺 Prompt Doctor",

        "detector":
            "🎯 كاشف AI",

        "image":
            "🖼️ Prompt صورة",

        "video":
            "🎬 Prompt فيديو",

        "persian":
            "🌍 فارسی → Pro Prompt",

        "remix":
            "🔄 إعادة صياغة Prompt",

        "generator_title":
            "🧠 مولد Prompt",

        "generator_help": (
            "🧠 مولد Prompt\n\n"
            "استخدم هذا القسم لإنشاء Prompts احترافية "
            "لمهام مختلفة.\n\n"
            "اختر نوع المهمة أولاً، ثم اشرح فكرتك بالتفصيل.\n\n"
            "💡 كلما قدمت تفاصيل أكثر، كانت النتيجة أفضل.\n\n"
            "مثال ضعيف:\n"
            "❌ اصنع شعاراً\n\n"
            "مثال قوي:\n"
            "✅ Create a modern minimalist logo for a "
            "technology brand called Nova, using a clean "
            "geometric symbol and a premium professional style.\n\n"
            "👇 اختر نوع Prompt:"
        ),

        "logo":
            "🎨 Logo / Design",

        "social":
            "📱 Social Media",

        "writing":
            "✍️ Writing",

        "other":
            "🔧 Other",

        "send_idea_general": (
            "✍️ أرسل فكرتك مع أكبر قدر ممكن من التفاصيل.\n\n"
            "💡 للحصول على نتيجة أفضل، اذكر:\n"
            "• ما هو هدفك؟\n"
            "• ما هو الموضوع بالتحديد؟\n"
            "• ما هو الأسلوب المطلوب؟\n"
            "• من هو الجمهور؟\n"
            "• هل توجد شروط أو قيود؟\n\n"
            "❌ فكرة ضعيفة:\n"
            "«أنشئ منشوراً»\n\n"
            "✅ فكرة قوية:\n"
            "«أنشئ منشور إطلاق منتج جديد على Instagram "
            "للجمهور من 18 إلى 30 سنة، بأسلوب ودود واحترافي "
            "مع Hook قوي في البداية.»\n\n"
            "🚀 المزيد من التفاصيل = Prompt أكثر احترافية.\n\n"
            "👇 أرسل فكرتك:"
        ),

        "image_help": (
            "🖼️ Prompt صورة\n\n"
            "هذه الميزة مخصصة لإنشاء Prompts احترافية "
            "لتوليد الصور بالذكاء الاصطناعي.\n\n"
            "أركز على الموضوع، البيئة، الإضاءة، التكوين، "
            "زاوية الكاميرا، الألوان، الأسلوب والأجواء.\n\n"
            "❌ فكرة ضعيفة:\n"
            "«سيارة جميلة»\n\n"
            "✅ فكرة قوية:\n"
            "«سيارة رياضية سوداء فاخرة في شوارع طوكيو "
            "الممطرة ليلاً، أضواء نيون وانعكاسات على الأسفلت "
            "الرطب، بتكوين سينمائي من زاوية منخفضة.»\n\n"
            "💡 كلما أضفت تفاصيل بصرية أكثر، أصبح Prompt أفضل.\n\n"
            "✍️ أرسل فكرة الصورة:"
        ),

        "video_help": (
            "🎬 Prompt فيديو\n\n"
            "هذه الميزة مخصصة لإنشاء Prompts احترافية "
            "لتوليد الفيديو بالذكاء الاصطناعي.\n\n"
            "أركز على حركة الشخص أو الشيء، حركة الكاميرا، "
            "الإضاءة، البيئة، الزمن والأسلوب السينمائي.\n\n"
            "❌ فكرة ضعيفة:\n"
            "«سيارة تتحرك في المدينة»\n\n"
            "✅ فكرة قوية:\n"
            "«سيارة رياضية حمراء تسير في شوارع دبي ليلاً، "
            "والكاميرا تتراجع ببطء من الأمام، مع انعكاس "
            "أضواء المدينة على السيارة وحركة سينمائية ناعمة.»\n\n"
            "💡 اشرح الحركة والجو بالتفصيل للحصول على Prompt أفضل.\n\n"
            "✍️ أرسل فكرة الفيديو:"
        ),

        "logo_help": (
            "🎨 Logo / Design\n\n"
            "هذه الميزة لإنشاء Prompts احترافية للشعارات "
            "والهوية البصرية والتصميم.\n\n"
            "❌ ضعيف:\n"
            "«اصنع شعاراً جيداً لشركة»\n\n"
            "✅ قوي:\n"
            "«أنشئ شعاراً حديثاً وبسيطاً لعلامة تقنية "
            "تسمى Nova، باستخدام رمز هندسي ومظهر فاخر "
            "مناسب للتطبيقات ووسائل التواصل الاجتماعي.»\n\n"
            "💡 اذكر اسم العلامة ومجالها وأسلوبها والألوان.\n\n"
            "✍️ أرسل فكرة التصميم:"
        ),

        "social_help": (
            "📱 Social Media\n\n"
            "هذه الميزة لإنشاء Prompts احترافية لمحتوى "
            "وسائل التواصل الاجتماعي.\n\n"
            "❌ ضعيف:\n"
            "«اصنع منشور Instagram»\n\n"
            "✅ قوي:\n"
            "«أنشئ وصفاً لمنشور Instagram لإطلاق منتج جديد "
            "للجمهور من 18 إلى 30 سنة، بأسلوب ودود واحترافي "
            "ويبدأ بجملة جذابة.»\n\n"
            "💡 اذكر المنصة والجمهور والموضوع والأسلوب.\n\n"
            "✍️ أرسل فكرة المحتوى:"
        ),

        "writing_help": (
            "✍️ Writing\n\n"
            "هذه الميزة لإنشاء Prompts احترافية للمقالات "
            "والقصص والكابتشن والإيميلات وغيرها.\n\n"
            "❌ ضعيف:\n"
            "«اكتب مقالاً عن الذكاء الاصطناعي»\n\n"
            "✅ قوي:\n"
            "«اكتب مقالاً تعليمياً من 1200 كلمة للمبتدئين "
            "حول تأثير الذكاء الاصطناعي على صناعة المحتوى، "
            "مع أمثلة حقيقية ولغة بسيطة.»\n\n"
            "💡 اذكر الموضوع والجمهور والطول والأسلوب والهدف.\n\n"
            "✍️ أرسل فكرتك:"
        ),

        "other_help": (
            "🔧 Other\n\n"
            "استخدم هذه الميزة للمهام التي لا تنتمي إلى "
            "الأقسام الأخرى.\n\n"
            "❌ ضعيف:\n"
            "«اصنع Prompt جيد»\n\n"
            "✅ قوي:\n"
            "«أريد خطة لتعلم اللغة الإنجليزية خلال ثلاثة أشهر "
            "لمتعلم متوسط يستطيع الدراسة ساعة واحدة يومياً.»\n\n"
            "💡 اشرح هدفك بالتفصيل.\n\n"
            "✍️ أرسل فكرتك:"
        ),

        "improve_help": (
            "🔥 تحسين Prompt\n\n"
            "أرسل Prompt موجوداً لديك.\n\n"
            "سأحسن الوضوح والبنية والتفاصيل والنتيجة المطلوبة.\n\n"
            "💡 إذا ذكرت الأداة أو المهمة التي سيستخدم فيها "
            "Prompt ستكون النتيجة أفضل.\n\n"
            "✍️ أرسل Prompt:"
        ),

        "doctor_help": (
            "🩺 Prompt Doctor\n\n"
            "أرسل Prompt الخاص بك.\n\n"
            "سأبحث عن المشاكل مثل الغموض أو نقص المعلومات "
            "أو ضعف البنية أو التعليمات غير الواضحة.\n\n"
            "ثم أقترح نسخة محسنة.\n\n"
            "✍️ أرسل Prompt:"
        ),

        "detector_help": (
            "🎯 كاشف AI\n\n"
            "أرسل النص وسأحلل العلامات التي قد تشير إلى "
            "أنه مكتوب بواسطة الذكاء الاصطناعي.\n\n"
            "⚠️ النتيجة ليست دليلاً مؤكداً بنسبة 100%.\n\n"
            "✍️ أرسل النص:"
        ),

        "persian_help": (
            "🌍 فارسی → Pro Prompt\n\n"
            "أرسل فكرتك باللغة الفارسية.\n\n"
            "سأفهم المعنى وأحولها إلى Prompt احترافي "
            "باللغة الإنجليزية بدلاً من ترجمتها حرفياً.\n\n"
            "✍️ أرسل فكرتك بالفارسية:"
        ),

        "remix_help": (
            "🔄 Prompt Remix\n\n"
            "أرسل Prompt الخاص بك.\n\n"
            "سأحافظ على الفكرة الأساسية وأعيد صياغتها "
            "ببنية وأسلوب مختلفين.\n\n"
            "✍️ أرسل Prompt:"
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

        "back":
            "🔙 رجوع",

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
# SIMPLE BACK KEYBOARD
# =========================================================

def back_keyboard(lang):

    t = TEXTS[lang]

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                t["back"],
                callback_data="home"
            )
        ]

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
# GEMINI INSTRUCTIONS
# =========================================================

def get_instruction(prompt_type):

    if prompt_type == "image":

        return """
You are an expert AI image prompt engineer.

Create a highly effective English prompt for an
AI image generation model.

Focus specifically on visual information:

- subject
- environment
- composition
- camera angle
- lens or perspective when useful
- lighting
- colors
- materials
- textures
- atmosphere
- visual style
- important visual details

Do not turn it into a video prompt.
Do not include motion or camera movement unless
it is relevant to describing a still image.

Output ONLY the final English prompt.
"""

    if prompt_type == "video":

        return """
You are an expert AI video prompt engineer.

Create a highly effective English prompt for an
AI video generation model.

Focus specifically on:

- subject
- environment
- action
- movement
- camera movement
- camera perspective
- lighting
- atmosphere
- timing
- pacing
- cinematic style
- visual continuity

Do not turn it into a still-image prompt.
Describe meaningful motion and camera behavior.

Output ONLY the final English prompt.
"""

    if prompt_type == "logo":

        return """
You are an expert logo and visual identity prompt engineer.

Create a professional English prompt for an AI
logo or graphic design generator.

Focus on:

- brand concept
- symbolism
- visual identity
- composition
- typography when relevant
- colors
- geometry
- design style
- simplicity
- scalability
- professional presentation

Output ONLY the final English prompt.
"""

    if prompt_type == "social":

        return """
You are an expert social media content prompt engineer.

Create a professional English prompt for generating
social media content.

Focus on:

- platform
- target audience
- objective
- hook
- tone
- structure
- content format
- engagement
- call to action when appropriate

Output ONLY the final English prompt.
"""

    if prompt_type == "writing":

        return """
You are an expert writing prompt engineer.

Create a professional English prompt for an AI writing assistant.

Clearly define:

- role
- objective
- topic
- context
- target audience
- tone
- structure
- length
- requirements
- desired output

Output ONLY the final English prompt.
"""

    if prompt_type == "persian":

        return """
You are an expert prompt engineer specializing in
turning Persian ideas into professional English prompts.

Understand the user's Persian meaning and intention.

Do NOT translate literally.

Instead, transform the idea into a natural,
professional and highly useful English prompt.

Preserve the user's intended meaning.
Do not invent unnecessary requirements.

Output ONLY the final English prompt.
"""

    if prompt_type == "remix":

        return """
You are an expert prompt engineer.

Rewrite the user's existing prompt into a stronger
and more polished English version.

Preserve the original concept and intention.

Improve:

- clarity
- structure
- specificity
- professional wording
- usefulness

Do not change the core meaning unnecessarily.

Output ONLY the final English prompt.
"""

    if prompt_type == "improve":

        return """
You are an expert prompt engineer.

Improve the user's existing prompt.

Keep the original goal but make it clearer,
more specific, structured and effective.

Do not add unnecessary requirements.

Output ONLY the improved English prompt.
"""

    if prompt_type == "doctor":

        return """
You are an expert prompt engineer and prompt reviewer.

Analyze the user's prompt internally.

Identify ambiguity, missing information,
weak instructions and structural problems.

Then produce a corrected and professional
English version.

Output ONLY the final improved English prompt.
"""

    if prompt_type == "detector":

        return """
You are an AI-writing analysis specialist.

Analyze the user's text for patterns commonly
associated with AI-generated writing.

Provide a concise analysis with:

- estimated likelihood
- important signals
- explanation

Do not claim certainty.

The response may be in the user's language.
"""

    return """
You are PromptPilot, a professional AI prompt engineer.

Understand the user's goal and create a useful,
clear and professional English prompt.

Do not translate literally.

Improve clarity and structure.

Do not invent unnecessary requirements.

Output ONLY the final English prompt.
"""


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

    instruction = get_instruction(
        prompt_type
    )

    full_prompt = f"""
You are PromptPilot.

{instruction}

IMPORTANT RULES:

1. Understand the user's actual intention.
2. Do not translate literally.
3. Improve clarity and usefulness.
4. Do not invent unnecessary requirements.
5. For prompt-generation features, the final prompt MUST be in English.
6. Do not explain your work.
7. Do not add "Prompt:" before the result.
8. Do not use markdown code fences.
9. Return only the requested final output.

USER INPUT:

{idea}
"""

    generating_message = await update.message.reply_text(
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

        user_states.setdefault(
            user_id,
            {}
        )

        user_states[user_id]["last_prompt"] = result

        # IMPORTANT:
        # Send result as a NEW message.
        # Do not edit the user's previous message.

        await update.message.reply_text(
            TEXTS[lang]["result"] + result,
            reply_markup=result_keyboard(lang)
        )

        try:
            await generating_message.delete()
        except Exception:
            pass

    except Exception as e:

        logger.error(
            "Gemini error: %s",
            e,
            exc_info=True
        )

        try:
            await generating_message.edit_text(
                TEXTS[lang]["error"]
            )
        except Exception:

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

    # =====================================================
    # LANGUAGE
    # =====================================================

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

    # =====================================================
    # GENERAL PROMPT GENERATOR
    # =====================================================

    if data == "feature_generator":

        user_states[user_id] = {
            "mode": "generator"
        }

        await query.edit_message_text(
            t["generator_help"],
            reply_markup=generator_type_keyboard(lang)
        )

        return

    # =====================================================
    # IMAGE PROMPT
    # =====================================================

    if data == "feature_image":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "image"
        }

        await query.edit_message_text(
            t["image_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # VIDEO PROMPT
    # =====================================================

    if data == "feature_video":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "video"
        }

        await query.edit_message_text(
            t["video_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # PROMPT IMPROVER
    # =====================================================

    if data == "feature_improver":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "improve"
        }

        await query.edit_message_text(
            t["improve_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # PROMPT DOCTOR
    # =====================================================

    if data == "feature_doctor":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "doctor"
        }

        await query.edit_message_text(
            t["doctor_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # AI DETECTOR
    # =====================================================

    if data == "feature_detector":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "detector"
        }

        await query.edit_message_text(
            t["detector_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # PERSIAN TO PRO PROMPT
    # =====================================================

    if data == "feature_persian":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "persian"
        }

        await query.edit_message_text(
            t["persian_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # PROMPT REMIX
    # =====================================================

    if data == "feature_remix":

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "remix"
        }

        await query.edit_message_text(
            t["remix_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # GENERATOR TYPES
    # =====================================================

    if data.startswith("type_"):

        selected_type = data.replace(
            "type_",
            ""
        )

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": selected_type
        }

        if selected_type == "logo":

            help_text = t["logo_help"]

        elif selected_type == "social":

            help_text = t["social_help"]

        elif selected_type == "writing":

            help_text = t["writing_help"]

        else:

            help_text = t["other_help"]

        await query.edit_message_text(
            help_text,
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # RESULT ACTION - IMPROVE
    # =====================================================

    if data == "action_improve":

        last_prompt = user_states.get(
            user_id,
            {}
        ).get(
            "last_prompt"
        )

        if not last_prompt:

            await query.answer(
                "No previous prompt found.",
                show_alert=True
            )

            return

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "improve",
            "source_prompt": last_prompt
        }

        await query.message.reply_text(
            "🔥 " + t["improve_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # RESULT ACTION - REMIX
    # =====================================================

    if data == "action_remix":

        last_prompt = user_states.get(
            user_id,
            {}
        ).get(
            "last_prompt"
        )

        if not last_prompt:

            await query.answer(
                "No previous prompt found.",
                show_alert=True
            )

            return

        user_states[user_id] = {
            "mode": "generator",
            "prompt_type": "remix",
            "source_prompt": last_prompt
        }

        await query.message.reply_text(
            "🔄 " + t["remix_help"],
            reply_markup=back_keyboard(lang)
        )

        return

    # =====================================================
    # HOME
    # =====================================================

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
