import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAudio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# --- الإعدادات الأساسية ---
ADMIN_ID = 5822683177  # !!! استبدله بـ ID الخاص بك !!!
TOKEN = "8319395629:AAHGS0jsCOVsxhqxS4rdWItLPB-7h-80qT8"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- وظائف إدارة البيانات والملفات ---

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

# --- لوحات المفاتيح (Keyboards) ---

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📖 أجزاء القرآن (الأثمان)", callback_data='menu_parts')],
        [InlineKeyboardButton("🎧 تلاوات خاشعة", callback_data='menu_reciters')],
        [InlineKeyboardButton("🔔 التنبيه اليومي", callback_data='menu_notif')]
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
        [InlineKeyboardButton("الشيخ المنشاوي", callback_data='rec_minshawi')],
        [InlineKeyboardButton("الشيخ الحصري", callback_data='rec_hussary')],
        [InlineKeyboardButton("⬅️ عودة", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- معالجات الأوامر (Handlers) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text("✨ مرحباً بك في بوت القرآن الكريم ✨", reply_markup=main_menu())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الإحصائيات (أدمن فقط)"""
    if update.effective_user.id != ADMIN_ID: return
    users = get_users()
    await update.message.reply_text(f"📊 عدد المستخدمين الحالي: {len(users)}")

async def reload_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تحميل البيانات (أدمن فقط)"""
    if update.effective_user.id != ADMIN_ID: return
    # بما أن load_quran_data تُستدعى عند كل طلب، فمجرد رسالة التأكيد كافية
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

async def send_daily_ayah(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(context.job.chat_id, text="☀️ آية اليوم: {وَقُل رَّبِّ زِدْنِي عِلْمًا}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'main_menu':
        await query.edit_message_text("اختر الخدمة:", reply_markup=main_menu())
    elif data == 'menu_parts':
        await query.edit_message_text("اختر الجزء:", reply_markup=parts_menu())
    elif data == 'menu_reciters':
        await query.edit_message_text("اختر القارئ:", reply_markup=reciters_menu())
    elif data == 'menu_notif':
        context.job_queue.run_repeating(send_daily_ayah, interval=86400, first=10, chat_id=query.message.chat_id)
        await query.edit_message_text("✅ تم تفعيل التنبيه اليومي!")
    
    elif data.startswith("send_part_"):
        part_num = data.split("_")[2]
        all_data = load_quran_data()
        key = f"part_{part_num}"
        
        # البحث عن الجزء داخل الملف
        source = all_data.get("quran_parts", all_data)
        
        if key in source:
            ids = source[key]
            await query.message.reply_text(f"⏳ جاري إرسال أثمان الجزء {part_num}...")

            # تقسيم الـ 16 ملف إلى مجموعتين (كل مجموعة 8)
            # لتجنب حظر تلجرام للرسائل الكبيرة
            chunk_size = 8
            for i in range(0, len(ids), chunk_size):
                chunk = ids[i:i + chunk_size]
                album = [InputMediaAudio(f_id, caption=f"ج {part_num} - الشيخ عبد الحميد القريو\nبواسطة @Suhayb_27_bot") for j, f_id in enumerate(chunk)]
                
                try:
                    await query.message.reply_media_group(media=album)
                except Exception as e:
                    await query.message.reply_text(f"❌ حدث خطأ أثناء إرسال هذه المجموعة: {e}")
        else:
            await query.message.reply_text(f"⚠️ الجزء {part_num} غير مضاف في البيانات بعد.")

# ضعه قبل سطر if __name__ == '__main__':
async def get_id(update, context):
    if update.message.audio:
        file_id = update.message.audio.file_id
        await update.message.reply_text(f"✅ تم استخراج الـ ID:\n\n`{file_id}`", parse_mode='MarkdownV2')

# --- التشغيل ---

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("bc", broadcast))
    app.add_handler(CommandHandler("reload", reload_config)) # السطر الجديد الخاص بالتحديث
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # داخل دالة main (بإزاحة 4 فراغات)
    app.add_handler(CommandHandler("reload", reload_config))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # أضف هذا السطر مرة واحدة فقط بهذا الشكل
    app.add_handler(MessageHandler(filters.AUDIO, get_id))

    print("🚀 البوت يعمل الآن بنجاح...")
    app.run_polling()

