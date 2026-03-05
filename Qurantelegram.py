import logging
import json
import uuid
import re
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAudio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram import InlineQueryResultAudio
from telegram.ext import InlineQueryHandler


TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ignored_words = ["سورة", "الشيخ", "القارئ", "قرآن","تلاوة", "قرأن" ]

def clean_text(text):
    if not text: return ""

    text = text.strip().lower()

    for word in ignored_words:
        text = text.replace(word, "")

    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[إأآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)

    return text.strip()


def save_user(user_id):
    """حفظ المستخدم الجديد وتجنب التكرار"""
    users = get_users()
    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{user_id}\n")

def get_users():
    """قراءة قائمة المستخدمين"""
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

def load_quran_data():
    """تحميل البيانات من ملف data.json"""
    try:
        if os.path.exists('data.json'):
            with open('data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"خطأ في JSON: {e}")
        return {}


def main_menu():
    keyboard = [
        [InlineKeyboardButton("ختمة كاملة (أثمان)🎧", callback_data='menu_parts')],
        [InlineKeyboardButton(" تلاوات خاشعة🎧", callback_data='menu_reciters')],
        [InlineKeyboardButton("المصحف📖", callback_data='menu_quran_options')]
    ]
    return InlineKeyboardMarkup(keyboard)

def parts_menu():
    keyboard = []
    for i in range(1, 31, 3):
        row = [
            InlineKeyboardButton(f"ج {i}", callback_data=f"send_part_{i}"),
            InlineKeyboardButton(f"ج {i+1}", callback_data=f"send_part_{i+1}"),
            InlineKeyboardButton(f"ج {i+2}", callback_data=f"send_part_{i+2}")
        ]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ عودة للقائمة الرئيسية", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

def reciters_menu():
    keyboard = [
        [InlineKeyboardButton("فهرس القراء🎙", callback_data='recta')],
        [InlineKeyboardButton("سور القرأن الكريم🎧", callback_data='recta_sora')],
        [InlineKeyboardButton("البحث بإستخدام الكلمات🌟", callback_data='recta_baht')],
        [InlineKeyboardButton("⬅️ عودة", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def quran_options_menu():
    keyboard = [
        [InlineKeyboardButton("القرآن مقسم أجزاء📚", callback_data='Quran_patts')],
        [InlineKeyboardButton("المصحف كامل📖", callback_data='quran_full')],
        [InlineKeyboardButton("⬅️ عودة", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def suhayb_qqq():
    keyboard = [
        [InlineKeyboardButton("⬅️ عودة", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def recta_five():
    keyboard = [
        [InlineKeyboardButton("ماهر المعيقلي", callback_data='mahert')],
        [InlineKeyboardButton("ياسر الدوسري", callback_data='yasert')],
        [InlineKeyboardButton("مشاري راشد العفاسي", callback_data='masharet')],
        [InlineKeyboardButton("بدر التركي", callback_data='badert')],
        [InlineKeyboardButton("بندر بليلة", callback_data='bandert')],
        [InlineKeyboardButton("⬅️ عودة", callback_data='reciters_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def parts_pdf():
    keyboard = []
    for i in range(1, 31, 3):
        row = [
            InlineKeyboardButton(f"ج {i}", callback_data=f"send_pdf_{i}"),
            InlineKeyboardButton(f"ج {i+1}", callback_data=f"send_pdf_{i+1}"),
            InlineKeyboardButton(f"ج {i+2}", callback_data=f"send_pdf_{i+2}")
        ]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ عودة للقائمة الرئيسية", callback_data='menu_quran_options')])
    return InlineKeyboardMarkup(keyboard)

async def create_maher_keyboard(page=0):
    data = load_quran_data()
    maher_data = data.get('reciters', {}).get('maher_muaiqly', [])

    total_surahs = len(maher_data)
    keyboard = []
    start = page * 10
    end = start + 10

    current_row = []
    for i in range(start, min(end, total_surahs)):
        surah_display_text = f"{i + 1}"
        s_name = maher_data[i].get('surah', 'غير معروف')
        button = InlineKeyboardButton(text=f" {surah_display_text}- سورة {s_name}", callback_data=f"playmaher_{i}")
        current_row.append(button)

        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"maherpage_{page-1}"))
    if end < total_surahs:
        nav_btns.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"maherpage_{page+1}"))

    if nav_btns:
        keyboard.append(nav_btns)

    return InlineKeyboardMarkup(keyboard)

async def create_yaser_keyboard(page=0):
    data = load_quran_data()
    yasser_data = data.get('reciters', {}).get('Yasser_dosare', [])

    total_surahs = len(yasser_data)
    keyboard = []
    start = page * 10
    end = start + 10

    current_row = []
    for i in range(start, min(end, total_surahs)):
        surah_display_text = f"{i + 1}"
        s_name = yasser_data[i].get('surah', 'غير معروف')
        button = InlineKeyboardButton(text=f" {surah_display_text}- سورة {s_name}", callback_data=f"playyaser_{i}")
        current_row.append(button)

        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"yaserpage_{page-1}"))
    if end < total_surahs:
        nav_btns.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"yaserpage_{page+1}"))

    if nav_btns:
        keyboard.append(nav_btns)

    return InlineKeyboardMarkup(keyboard)




async def create_bander_keyboard(page=0):
    data = load_quran_data()
    reciters = data.get('reciters', {})
    bander_data = reciters.get('bander_balela')

    if bander_data is None:
        bander_data = data.get('bander_balela', [])
    total_surahs = len(bander_data)

    print(f"📊 DEBUG: Found {total_surahs} surahs for Bander Balela")


    keyboard = []
    start = page * 10
    end = start + 10

    current_row = []
    for i in range(start, min(end, total_surahs)):
        surah_display_text = f"{i + 1}"
        s_name = bander_data[i].get('surah', 'غير معروف')

        button = InlineKeyboardButton(
            text=f"{surah_display_text} - سورة {s_name}",
            callback_data=f"playbander_{i}"
        )
        current_row.append(button)

        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"banderpage_{page-1}"))

    if end < total_surahs:
        nav_btns.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"banderpage_{page+1}"))

    if nav_btns:
        keyboard.append(nav_btns)

    return InlineKeyboardMarkup(keyboard)

async def create_mashare_keyboard(page=0):
    data = load_quran_data()
    mashare_data = data.get('reciters', {}).get('mashare_rashed', [])

    total_surahs = len(mashare_data)
    keyboard = []
    start = page * 10
    end = start + 10

    current_row = []
    for i in range(start, min(end, total_surahs)):
        surah_display_text = f"{i + 1}"
        s_name = mashare_data[i].get('surah', 'غير معروف')
        button = InlineKeyboardButton(text=f" {surah_display_text}- سورة {s_name}", callback_data=f"playmashare_{i}")
        current_row.append(button)

        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"masharepage_{page-1}"))
    if end < total_surahs:
        nav_btns.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"masharepage_{page+1}"))

    if nav_btns:
        keyboard.append(nav_btns)

    return InlineKeyboardMarkup(keyboard)

async def create_badder_keyboard(page=0):
    data = load_quran_data()
    badder_data = data.get('reciters', {}).get('badder_turke', [])

    total_surahs = len(badder_data)
    keyboard = []
    start = page * 10
    end = start + 10

    current_row = []
    for i in range(start, min(end, total_surahs)):
        surah_display_text = f"{i + 1}"
        s_name = badder_data[i].get('surah', 'غير معروف')
        button = InlineKeyboardButton(text=f" {surah_display_text}- سورة {s_name}", callback_data=f"playbadder_{i}")
        current_row.append(button)

        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"badderpage_{page-1}"))
    if end < total_surahs:
        nav_btns.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"badderpage_{page+1}"))

    if nav_btns:
        keyboard.append(nav_btns)

    return InlineKeyboardMarkup(keyboard)

async def create_surah_index_keyboard(page=0):
    all_surahs = ["الفاتحة", "البقرة", "ال عمران", "النساء", "المائدة", "الانعام", "الاعراف", "الانفال", "التوبة", "يونس", "هود", "يوسف", "الرعد", "ابراهيم", "الحجر", "النحل", "الاسراء", "الكهف", "مريم", "طه", "الانبياء", "الحج", "المؤمنيون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم", "لقمان", "السجدة", "الاحزاب", "سبا", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر", "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الاحقاف", "محمد", "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر",
"الممتحنة", "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم",
"الحاقة", "المعارج", "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الانسان", "المرسلات", "النبأ", "النازعات",
 "عبس", "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية",
"الفجر", "البلد", "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة",
 "العاديات", "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص", "الفلق", "الناس"]

    keyboard = []
    start = page * 10
    end = start + 10

    current_row = []
    for i in range(start, min(end, len(all_surahs))):
        surah_name = all_surahs[i]

        display_text = f"{i + 1}. {surah_name}"

        button = InlineKeyboardButton(text=display_text, callback_data=f"search_{surah_name}")
        current_row.append(button)

        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton(text="⬅️ السابق", callback_data=f"idxpage_{page-1}"))
    if end < len(all_surahs):
        nav_btns.append(InlineKeyboardButton(text="التالي ➡️", callback_data=f"idxpage_{page+1}"))

    if nav_btns:
        keyboard.append(nav_btns)

    return InlineKeyboardMarkup(keyboard)


    return InlineKeyboardMarkup(keyboard)
async def change_index_page(update, context):
    query = update.callback_query
    await query.answer()

    try:
        page = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        page = 0

    markup = await create_surah_index_keyboard(page=page)

    await query.edit_message_text(
        text=f"📖 فهرس السور - صفحة {page + 1}",
        reply_markup=markup
    )







async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text("🤍  مرحباً بك في بوت القرآن الكريم 🤍", reply_markup=main_menu())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الإحصائيات (أدمن فقط)"""
    if update.effective_user.id != ADMIN_ID: return
    users = get_users()
    await update.message.reply_text(f"📊 عدد المستخدمين الحالي: {len(users)}")

async def reload_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تحميل البيانات (أدمن فقط)"""
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("✅ تم تحديث النظام وقراءة ملف data.json بنجاح!")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إذاعة ذكية مع تنظيف القائمة"""
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("📝 استخدم: `/bc نص الرسالة`")
        return

    msg = " ".join(context.args)
    users = get_users()
    active_users = []
    sent_count = 0
    await update.message.reply_text(f"⏳ جاري الإرسال لـ {len(users)} مستخدم...")

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            active_users.append(uid)
            sent_count += 1
        except: continue

    with open("users.txt", "w") as f:
        for uid in active_users: f.write(f"{uid}\n")
    await update.message.reply_text(f"✅ تم الإرسال لـ {sent_count} وتنظيف القائمة.")

async def inline_query(update, context):
    global data
    query = update.inline_query.query.strip()
    if not query:
        return

    results = []
    clean_query = clean_text(query)

    for reciter_key, surahs in data.get("reciters", {}).items():
        for surah in surahs:
            full_name = clean_text(f"{surah['surah']} {surah['reciter']}")

            if clean_query in full_name and surah['audio_id']:
                results.append(
                    InlineQueryResultAudio(
                        id=str(uuid.uuid4()),
                        audio_url=surah['audio_id'],
                        title=f"{surah['surah']} - {surah['reciter']}"
                    )
                )

    await update.inline_query.answer(results[:10])


async def send_daily_ayah(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.chat_id, text="☀️ آية اليوم: {وَقُل رَّبِّ زِدْنِي عِلْمًا}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'main_menu':
        await query.edit_message_text("اختر بإستخدام الأزرار في الأسفل:", reply_markup=main_menu())
    elif data == 'menu_parts':
        await query.edit_message_text("ختمة الشيخ عبد الحميد القريو\nاختر الجزء ليتم إرسال الأثمان:", reply_markup=parts_menu())
    elif data == 'menu_reciters':
        await query.edit_message_text("اختر من القوائم الخاصة بالقراء أو من خلال فهرس السور.\nأو يمكنك كتابة إسم القارئ و إسم السورة لتسهيل عملية البحث🌟", reply_markup=reciters_menu())
    elif data == 'menu_quran_options':
        await query.edit_message_text("اختر من القائمة:", reply_markup=quran_options_menu())
    elif data == 'Quran_patts':
        await query.edit_message_text(
            text="📖 اختر الجزء الذي تريد قرأته PDF:",
            reply_markup=parts_pdf())
    elif data == 'recta':
        await query.edit_message_text("اختر القارئ الذي تحب الإستماع له:", reply_markup=recta_five())

    elif data == 'recta_sora':
        markup = await create_surah_index_keyboard(page=0)
        await query.edit_message_text(
            text="📖 فهرس سور القرآن الكريم\nاختر السورة للاستماع لجميع القراء المتوفرين:",
            reply_markup=markup
        )

    elif data == 'recta_baht':
        await query.edit_message_text("البحث عن ملف🌟\nيمكنك البحث عن اي ملف بإستخدام إسم القارئ و إسم السورة مثلاً:سورة الفاتحة الشيخ بندر بليلة \n\nقائمة القراء المتوفرين حالياً\n-ماهر المعيقلي. \n-مشاري راشد العفاسي \n-ياسر الدوسري \n-بدر التركي \n-بندر بليلة \n\n @SBT1bot❄\n____", reply_markup=suhayb_qqq())



    elif data.startswith("send_part_"):
        part_num = data.split("_")[2]
        all_data = load_quran_data()
        key = f"part_{part_num}"

        source = all_data.get("quran_parts", all_data)

        if key in source:
            ids = source[key]
            await query.message.reply_text(f"⏳سيتم إرسال أثمان الجزء {part_num}...")

            chunk_size = 8
            for i in range(0, len(ids), chunk_size):
                chunk = ids[i:i + chunk_size]
                album = [InputMediaAudio(f_id, caption=f"ج {part_num} - الشيخ عبد الحميد القريو\nبواسطة: @SBT1bot") for j, f_id in enumerate(chunk)]

                try:
                    await query.message.reply_media_group(media=album)
                except Exception as e:
                    await query.message.reply_text(f"❌ حدث خطأ أثناء إرسال هذه المجموعة: {e}")
        else:
            await query.message.reply_text(f"⚠️ الجزء {part_num} غير مضاف في قاعدة البيانات بعد.")

    elif data.startswith("send_pdf_"):
        pdf_num = data.split("_")[2]
        all_data = load_quran_data()

        source = all_data.get("quran_pdf", {})

        if pdf_num in source:
            f_id = source[pdf_num]
            await query.message.reply_text(f"⏳ سيتم إرسال الجزء {pdf_num} (PDF)...")

            try:
                await query.message.reply_document(
                    document=f_id.strip(),
                    caption=f"📖 المصحف الشريف - الجزء {pdf_num}\n@SBT1bot❄️"
                )
            except Exception as e:
                await query.message.reply_text(f"❌ حدث خطأ أثناء إرسال الملف: {e}")
        else:
            await query.message.reply_text(f"❌ الجزء {pdf_num} غير موجود في قاعدة البيانات")

    elif data == 'quran_full':
        all_data = load_quran_data()
        q_list = all_data.get("full_quran_list", [])

        if q_list:
            await query.message.reply_text("⏳ سيتم إرسال المصحف الشريف...")
            for item in q_list:
                try:
                    f_id = item.get("file_id", "").strip()
                    cap = item.get("caption", "المصحف الشريف")

                    await query.message.reply_document(
                        document=f_id,
                        caption=f"{cap}\n\nبواسطة: @SBT1bot"
                    )
                except Exception as e:
                    await query.message.reply_text(f"❌ خطأ في إرسال ملف: {e}")
        else:
            await query.message.reply_text("⚠️ القائمة فارغة في قاعدة البيانات")


async def start_maher(update, context):
    query = update.callback_query
    await query.answer()
    markup = await create_maher_keyboard(page=0)
    await query.edit_message_text(
        text="📖 ختمة الشيخ ماهر المعيقلي - اختر السورة:",
        reply_markup=markup
    )

async def change_maher_page(update, context):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[1])
    markup = await create_maher_keyboard(page=page)
    await query.edit_message_text(
        text=f"🎙 ختمة الشيخ ماهر - صفحة {page + 1}",
        reply_markup=markup
    )

async def play_surah(update, context):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    data = load_quran_data()

    maher_list = data.get('reciters', {}).get('maher_muaiqly', [])

    if index < len(maher_list):
        surah_item = maher_list[index]

        audio_id = surah_item.get('audio_id')
        surah_name = surah_item.get('surah', 'غير معروف')

        try:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_id,
                caption=f"🎙️ سورة {surah_name} تلاوة الشيخ ماهر المعيقلي\n\n@SBT1bot❄️"
            )
        except Exception as e:
            await query.message.reply_text(f"❌ حدث خطأ أثناء إرسال السورة: {e}")
    else:
        await query.message.reply_text("⚠️ عذراً، لم يتم العثور على بيانات هذه السورة.")



async def start_yaser(update, context):
    query = update.callback_query
    await query.answer()
    markup = await create_yaser_keyboard(page=0)
    await query.edit_message_text(
        text="🎙 ختمة الشيخ ياسر الدوسري - اختر السورة:",
        reply_markup=markup
    )
async def change_yaser_page(update, context):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[1])
    markup = await create_yaser_keyboard(page=page)
    await query.edit_message_text(
        text=f"ختمة الشيخ ياسر - صفحة {page + 1}",
        reply_markup=await create_bander_keyboard()
    )
async def play_surah_yaser(update, context):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    data = load_quran_data()

    yaser_list = data.get('reciters', {}).get('Yasser_dosare', [])

    if index < len(yaser_list):
        surah_item = yaser_list[index]
        audio_id = surah_item.get('audio_id')
        surah_name = surah_item.get('surah', 'غير معروف')

        try:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_id,
                caption=f"🎙️ سورة {surah_name} تلاوة الشيخ ياسر الدوسري\n\n@SBT1bot❄️"
            )
        except Exception as e:
            await query.message.reply_text(f"❌ خطأ في الإرسال: {e}")

async def start_bander(update, context):
    query = update.callback_query
    await query.answer()
    markup = await create_bander_keyboard(page=0)
    await query.edit_message_text(
        text="ختمة الشيخ بندر بليلة - اختر السورة:",
        reply_markup=markup
    )
                                                                                                                                                       async def change_bander_page(update, context):                                                                                                             query = update.callback_query                                                                                                                          await query.answer()
    page = int(query.data.split("_")[1])                                                                                                                   markup = await create_bander_keyboard(page=page)                                                                                                       await query.edit_message_text(                                                                                                                             text=f"ختمة الشيخ بندر بليلة - صفحة {page + 1}",                                                                                                       reply_markup=markup
    )                                                                                                                                                                                                                                                                                                         async def play_surah_bander(update, context):                                                                                                              query = update.callback_query                                                                                                                          await query.answer()
                                                                                                                                                           index = int(query.data.split("_")[1])                                                                                                                  data = load_quran_data()                                                                                                                               bander_list = data.get('reciters', {}).get('bander_balela', [])                                                                                                                                                                                                                                               if index < len(bander_list):                                                                                                                               surah_item = bander_list[index]                                                                                                                        audio_id = surah_item.get('audio_id')                                                                                                                  surah_name = surah_item.get('surah', 'غير معروف')                                                                                                                                                                                                                                                             try:                                                                                                                                                       await context.bot.send_audio(                                                                                                                              chat_id=query.message.chat_id,                                                                                                                         audio=audio_id,                                                                                                                                        caption=f"🎙️ سورة {surah_name} تلاوة الشيخ بندر بليلة\n\n@SBT1bot"                                                                                  )
        except Exception as e:                                                                                                                                     await query.message.reply_text(f"❌ خطأ في الإرسال: {e}")                                                                                                                                                                                                                                                                                                                                                                                                async def start_mashare(update, context):
    query = update.callback_query                                                                                                                          await query.answer()                                                                                                                                   markup = await create_mashare_keyboard(page=0)                                                                                                         await query.edit_message_text(                                                                                                                             text="ختمة الشيخ مشاري راشد العفاسي - اختر السورة:",                                                                                                   reply_markup=markup                                                                                                                                )                                                                                                                                                                                                                                                                                                         async def change_mashare_page(update, context):                                                                                                            query = update.callback_query                                                                                                                          await query.answer()                                                                                                                                   page = int(query.data.split("_")[1])                                                                                                                   markup = await create_mashare_keyboard(page=page)                                                                                                      await query.edit_message_text(                                                                                                                             text=f"ختمة الشيخ بندر بليلة - صفحة {page + 1}",                                                                                                       reply_markup=markup                                                                                                                                )                                                                                                                                                                                                                                                                                                         async def play_surah_mashare(update, context):                                                                                                             query = update.callback_query                                                                                                                          await query.answer()

    index = int(query.data.split("_")[1])                                                                                                                  data = load_quran_data()                                                                                                                               mashare_list = data.get('reciters', {}).get('mashare_rashed', [])                                                                                                                                                                                                                                             if index < len(mashare_list):                                                                                                                              surah_item = mashare_list[index]                                                                                                                       audio_id = surah_item.get('audio_id')                                                                                                                  surah_name = surah_item.get('surah', 'غير معروف')                                                                                                                                                                                                                                                             try:                                                                                                                                                       await context.bot.send_audio(                                                                                                                              chat_id=query.message.chat_id,                                                                                                                         audio=audio_id,                                                                                                                                        caption=f"🎙️ سورة {surah_name} تلاوة الشيخ مشاري راشد العفاسي\n\n@SBT1bot"                                                                          )                                                                                                                                                  except Exception as e:                                                                                                                                     await query.message.reply_text(f"❌ خطأ في الإرسال: {e}")
                                                                                                                                                                                                                                                                                                              async def start_badder(update, context):
    query = update.callback_query
    await query.answer()                                                                                                                                   markup = await create_badder_keyboard(page=0)                                                                                                          await query.edit_message_text(                                                                                                                             text="ختمة الشيخ بدر التركي - اختر السورة:",                                                                                                           reply_markup=markup                                                                                                                                )                                                                                                                                                                                                                                                                                                         async def change_badder_page(update, context):                                                                                                             query = update.callback_query                                                                                                                          await query.answer()                                                                                                                                   page = int(query.data.split("_")[1])                                                                                                                   markup = await create_badder_keyboard(page=page)                                                                                                       await query.edit_message_text(                                                                                                                             text=f"ختمة الشيخ بدر التركي - صفحة {page + 1}",                                                                                                       reply_markup=markup                                                                                                                                )                                                                                                                                                                                                                                                                                                         async def play_surah_badder(update, context):                                                                                                              query = update.callback_query                                                                                                                          await query.answer()                                                                                                                                                                                                                                                                                          index = int(query.data.split("_")[1])
    data = load_quran_data()                                                                                                                               badder_list = data.get('reciters', {}).get('badder_turke', [])                                                                                                                                                                                                                                                if index < len(badder_list):                                                                                                                               surah_item = badder_list[index]                                                                                                                        audio_id = surah_item.get('audio_id')                                                                                                                  surah_name = surah_item.get('surah', 'غير معروف')                                                                                                                                                                                                                                                             try:                                                                                                                                                       await context.bot.send_audio(                                                                                                                              chat_id=query.message.chat_id,                                                                                                                         audio=audio_id,                                                                                                                                        caption=f"🎙️ سورة {surah_name} تلاوة الشيخ بدر التركي\n\n@SBT1bot"                                                                                  )                                                                                                                                                  except Exception as e:                                                                                                                                     await query.message.reply_text(f"❌ خطأ في الإرسال: {e}")
                                                                                                                                                                                                                                                                                                              async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):                                                                                      if update.message.document:                                                                                                                                f_id = update.message.document.file_id
        text = f"✅ تم استخراج ID الملف:\n\n`{f_id}`"                                                                                                      elif update.message.audio:                                                                                                                                 f_id = update.message.audio.file_id                                                                                                                    text = f"✅ تم استخراج ID ملف الصوت:\n\n`{f_id}`"                                                                                                  else:
        return                                                                                                                                                                                                                                                                                                    await update.message.reply_text(text, parse_mode='Markdown')                                                                                                                                                                                                                                              async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = clean_text(update.message.text)                                                                                                           all_data = load_quran_data()                                                                                                                           found_results = []                                                                                                                                                                                                                                                                                            reciters_data = all_data.get("reciters", {})
    for r_key, surahs in reciters_data.items():                                                                                                                for surah in surahs:                                                                                                                                       s_name = clean_text(surah.get('surah', ''))                                                                                                            r_name = clean_text(surah.get('reciter', ''))                                                                                                          search_pool = f"{s_name} {r_name}"                                                                                                                                                                                                                                                                            if all(word in search_pool for word in user_query.split()):                                                                                                found_results.append(surah)                                                                                                                                                                                                                                                                       if found_results:                                                                                                                                          await update.message.reply_text(f"🔍 تم العثور على {len(found_results)} نتيجة:")                                                                       for res in found_results[:10]:                                                                                                                             try:                                                                                                                                                       await update.message.reply_audio(                                                                                                                          audio=res['audio_id'].strip(),                                                                                                                         caption=f"📖 سورة: {res['surah']}\n👤 القارئ: {res['reciter']}\n\n@SBT1bot"
                )                                                                                                                                                  except Exception as e:                                                                                                                                     continue                                                                                                                                   else:                                                                                                                                                      await update.message.reply_text("❌ لم أجد سورة بهذا الاسم أو القارئ. جرب مثلاً: 'البقرة المنشاوي'")
                                                                                                                                                                                                                                                                                                              async def handle_surah_search(update, context):                                                                                                            query = update.callback_query                                                                                                                          surah_name = query.data.split("_")[1]
    await query.answer(f"🔍 جاري البحث عن سورة {surah_name}...")                                                                                                                                                                                                                                                  data = load_quran_data()                                                                                                                               reciters = data.get('reciters', {})                                                                                                                    found_any = False
                                                                                                                                                           for reciter_id, surahs in reciters.items():                                                                                                                for item in surahs:                                                                                                                                        if item.get('surah') == surah_name:                                                                                                                        found_any = True
                audio_id = item.get('audio_id')                                                                                                                                                                                                                                                                               reciter_display_name = item.get('reciter', reciter_id.replace('_', ' ').title())                                                                                                                                                                                                                              try:                                                                                                                                                       await context.bot.send_audio(                                                                                                                              chat_id=query.message.chat_id,                                                                                                                         audio=audio_id,                                                                                                                                        caption=f"📖 سورة: {surah_name}\n🎙️ تلاوة الشيخ: {reciter_display_name}"                                                                            )                                                                                                                                                  except Exception as e:                                                                                                                                     print(f"❌ خطأ أثناء إرسال ملف: {e}")                                                                                                                                                                                                                                                         if not found_any:                                                                                                                                          await query.message.reply_text(f"لم يتم العثور على لسورة {surah_name}.")                                                                       
                                                                                                                                                                                                                                                                                                              if __name__ == '__main__':                                                                                                                                 app = ApplicationBuilder().token(TOKEN).build()                                                                                                    
    app.add_handler(CommandHandler("start", start))                                                                                                        app.add_handler(CommandHandler("stats", stats))                                                                                                        app.add_handler(CommandHandler("bc", broadcast))                                                                                                       app.add_handler(CommandHandler("reload", reload_config))                                                                                           
    app.add_handler(CallbackQueryHandler(start_maher, pattern="^mahert$"))                                                                                 app.add_handler(CallbackQueryHandler(change_maher_page, pattern="^maherpage_"))                                                                        app.add_handler(CallbackQueryHandler(play_surah, pattern="^playmaher_"))                                                                               app.add_handler(CallbackQueryHandler(start_yaser, pattern="^yasert$"))                                                                                 app.add_handler(CallbackQueryHandler(change_yaser_page, pattern="^yaserpage_"))
    app.add_handler(CallbackQueryHandler(play_surah_yaser, pattern="^playyaser_"))                                                                         app.add_handler(CallbackQueryHandler(start_bander, pattern="^bandert$"))                                                                               app.add_handler(CallbackQueryHandler(change_bander_page, pattern="^banderpage_"))                                                                      app.add_handler(CallbackQueryHandler(play_surah_bander, pattern="^playbander_"))                                                                       app.add_handler(CallbackQueryHandler(start_mashare, pattern="^masharet$"))                                                                             app.add_handler(CallbackQueryHandler(change_mashare_page, pattern="^masharepage_"))                                                                    app.add_handler(CallbackQueryHandler(play_surah_mashare, pattern="^playmashare_"))                                                                     app.add_handler(CallbackQueryHandler(start_badder, pattern="^badert$"))                                                                                app.add_handler(CallbackQueryHandler(change_badder_page, pattern="^badderpage_"))                                                                      app.add_handler(CallbackQueryHandler(play_surah_badder, pattern="^playbadder_"))                                                                       app.add_handler(CallbackQueryHandler(handle_surah_search, pattern="^search_"))                                                                         app.add_handler(CallbackQueryHandler(change_index_page, pattern="^idxpage_"))                                                                          app.add_handler(CallbackQueryHandler(handle_callback))                                                                                                 app.add_handler(InlineQueryHandler(inline_query))                                                                                                      app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_files))                                                                         app.add_handler(CommandHandler("reload", reload_config))                                                                                               app.add_handler(MessageHandler(filters.AUDIO | filters.Document.PDF, get_id))                                                                                                                                                                                                                                 print("🚀 البوت يعمل الآن بنجاح...")                                                                                                                   app.run_polling()
