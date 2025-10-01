from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3
import os
import random
import string
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN", "8338474041:AAHhb3kLsZ4eidcB1fCJchkLrNPRTGEvSFo")
CHANNEL_USERNAME = "@kasraltrnd1"
YOUR_ACCOUNT = "@kasraltrnd"
ADMIN_IDS = [8327186147]  # ✅ تم وضع أيديك هنا

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT, 
                  referrals INTEGER DEFAULT 0, 
                  free_signals INTEGER DEFAULT 0,
                  user_id_sent BOOLEAN DEFAULT FALSE,
                  completed_steps BOOLEAN DEFAULT FALSE,
                  referral_sent BOOLEAN DEFAULT FALSE,
                  completion_time TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS signal_codes
                 (code TEXT PRIMARY KEY,
                  user_id INTEGER,
                  username TEXT,
                  used BOOLEAN DEFAULT FALSE,
                  created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def generate_signal_code():
    """إنشاء كود توصية عشوائي"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def check_channel_membership(user_id, context):
    """التحقق إذا كان المستخدم منضم للقناة"""
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # حفظ المستخدم في Database
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()
    
    # التحقق إذا كانت بداية بإحالة
    if context.args and context.args[0].startswith('ref_'):
        referrer_id = int(context.args[0].split('_')[1])
        await handle_referral(user_id, referrer_id, context)
    
    welcome_message = (
        "مرحبًا بك في بوت كاسر الترند 🔥\n\n"
        "هل تبحث عن توصيات دقيقة وإشارات تداول موثوقة؟\n"
        "عالية الدقة تصل نسبة نجاحها إلى %95 📈"
    )

    keyboard = [
        [InlineKeyboardButton("نعم ✅", callback_data="yes"),
         InlineKeyboardButton("لا ❌", callback_data="no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def handle_referral(new_user_id, referrer_id, context):
    """معالجة الإحالة"""
    if new_user_id == referrer_id:
        return
    
    is_member = await check_channel_membership(new_user_id, context)
    
    if is_member:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE users SET referrals = referrals + 1, free_signals = free_signals + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()
        conn.close()
        
        try:
            await context.bot.send_message(
                referrer_id,
                f"🎉 **مبروك! إحالة ناجحة**\n\n"
                f"✅ صديقك انضم للقناة عبر رابطك\n"
                f"🎁 **حصلت على توصية مجانية جديدة!**\n\n"
                f"💡 استخدم /signal للحصول على كود التوصية\n"
                f"📊 شاهد إحصائياتك: /mysignals"
            )
        except:
            pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        # عرض الشروط والخطوات
        reply_text = (
            "🌟 **خطوات الانضمام:**\n\n"
            "🌟1️⃣ أولًا انضم إلينا في القناة التعليمية و احصل على:\n"
            "• خبرات عملية في مجال التداول. 📊\n"
            "• أقوى استراتيجيات التداول. 🧠\n"
            "• دعم مستمر لتطوير مستواك. 💪\n"
            "ابدأ رحلتك نحو الاحتراف الآن! 🚀\n\n"
            "رابط القناة: https://t.me/kasraltrnd1\n\n"
            "🌟2️⃣ ثانيًا قم بحذف حسابك وسجل حساب جديد من الرابط التالي:\n"
            "https://short-url.org/1grgn\n\n"
            "🌟3️⃣ بعد التسجيل من الرابط، أرسل الآيدي إلى هذا الحساب (@kasraltrnd) ."
        )
        
        # التحقق إذا كان المستخدم منضم للقناة
        is_member = await check_channel_membership(query.from_user.id, context)
        
        if not is_member:
            keyboard = [
                [InlineKeyboardButton("انضم للقناة أولاً 📢", url="https://t.me/kasraltrnd1")],
                [InlineKeyboardButton("تأكيد الانضمام ✅", callback_data="check_join")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚠️ **يجب الانضمام للقناة أولاً**\n\n"
                "انضم لقناتنا ثم اضغط 'تأكيد الانضمام':\n"
                "https://t.me/kasraltrnd1",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(reply_text)
            
            # طلب إدخال الآيدي
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📝 **الرجاء إرسال الآيدي الخاص بك الآن:**",
                parse_mode='Markdown'
            )
    
    elif query.data == "no":
        await query.edit_message_text("شكرًا لك ❤️☺️")
    
    elif query.data == "check_join":
        # التحقق من الانضمام مرة أخرى
        is_member = await check_channel_membership(query.from_user.id, context)
        
        if is_member:
            # إعادة عرض الشروط
            reply_text = (
                "🌟 **خطوات الانضمام:**\n\n"
                "🌟1️⃣ ✅ أنت منضم للقناة\n\n"
                "🌟2️⃣ ثانيًا قم بحذف حسابك وسجل حساب جديد من الرابط التالي:\n"
                "https://short-url.org/1grgn\n\n"
                "🌟3️⃣ بعد التسجيل من الرابط، أرسل الآيدي إلى هذا الحساب (@kasraltrnd) ."
            )
            await query.edit_message_text(reply_text)
            
            # طلب إدخال الآيدي
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📝 **الرجاء إرسال الآيدي الخاص بك الآن:**",
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ لم تنضم للقناة بعد!", show_alert=True)
    
    elif query.data == "get_signal_code":
        await signal_command(update, context)

async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إرسال الآيدي"""
    user_id = update.effective_user.id
    user_input = update.message.text
    
    # التحقق إذا كان المستخدم قد أرسل الآيدي مسبقاً
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id_sent, completed_steps FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result and result[0]:
        # إذا كان قد أرسل مسبقاً
        await update.message.reply_text("✅ لقد قمت بإرسال الآيدي مسبقاً!")
        
        # إذا لم يكمل الخطوات بعد، نتحقق
        if not result[1]:
            await check_user_completion(user_id, context)
        
        conn.close()
        return
    
    try:
        # التحقق من الانضمام للقناة
        is_member = await check_channel_membership(user_id, context)
        
        if not is_member:
            await update.message.reply_text(
                "❌ **يجب الانضمام للقناة أولاً**\n\n"
                "انضم للقناة ثم أعد إرسال الآيدي:\n"
                "https://t.me/kasraltrnd1"
            )
            conn.close()
            return
        
        # إرسال الآيدي إلى @kasraltrnd
        await context.bot.send_message(
            chat_id="@kasraltrnd",
            text=f"🎯 **آيدي جديد من مستخدم:**\n\n"
                 f"👤 User ID: `{user_id}`\n"
                 f"📛 Username: @{update.effective_user.username or 'لا يوجد'}\n"
                 f"🏷️ الاسم: {update.effective_user.first_name}\n"
                 f"📝 الآيدي المدخل: {user_input}",
            parse_mode='Markdown'
        )
        
        # تحديث قاعدة البيانات
        c.execute("UPDATE users SET user_id_sent = TRUE WHERE user_id = ?", (user_id,))
        conn.commit()
        
        # إرسال رسالة تأكيد للمستخدم
        await update.message.reply_text(
            "✅ **تم إرسال الآيدي بنجاح إلى @kasraltrnd**\n\n"
            "🎉 **تهانينا! لقد أكملت جميع الخطوات**\n\n"
            "⏰ **سأرسل لك رسالة نظام الإحالة بعد 24 ساعة**\n"
            "حيث يمكنك بدء كسب التوصيات المجانية!"
        )
        
        # تسجيل وقت إكمال الخطوات وبدء العد التنازلي
        completion_time = datetime.now()
        c.execute("UPDATE users SET completed_steps = TRUE, completion_time = ? WHERE user_id = ?", 
                  (completion_time, user_id))
        conn.commit()
        
        # جدولة رسالة الإحالة بعد 24 ساعة
        await schedule_referral_message(user_id, context, completion_time)
        
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ في الإرسال. حاول مرة أخرى.")
        print(f"Error: {e}")
    
    finally:
        conn.close()

async def check_user_completion(user_id, context):
    """التحقق من اكتمال خطوات المستخدم"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT completed_steps, completion_time FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:  # إذا اكتملت الخطوات
        completion_time = result[1]
        if isinstance(completion_time, str):
            completion_time = datetime.strptime(completion_time, '%Y-%m-%d %H:%M:%S')
        
        time_elapsed = datetime.now() - completion_time
        
        if time_elapsed.total_seconds() >= 24 * 3600:  # 24 ساعة
            # إرسال رسالة الإحالة فوراً
            await send_referral_message(context, user_id)
        else:
            # حساب الوقت المتبقي
            remaining = 24 * 3600 - time_elapsed.total_seconds()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            
            await context.bot.send_message(
                user_id,
                f"⏳ **الوقت المتبقي لرسالة الإحالة:** {hours} ساعة و {minutes} دقيقة\n\n"
                f"📊 يمكنك استخدام /mysignals لمشاهدة إحصائياتك"
            )

async def schedule_referral_message(user_id, context, completion_time):
    """جدولة رسالة الإحالة بعد 24 ساعة"""
    # حساب وقت الإرسال (بعد 24 ساعة)
    send_time = completion_time + timedelta(hours=24)
    
    # تخزين وقت الجدولة
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET completion_time = ? WHERE user_id = ?", (completion_time, user_id))
    conn.commit()
    conn.close()
    
    print(f"⏰ تم جدولة رسالة إحالة للمستخدم {user_id} بعد 24 ساعة")

async def check_pending_referrals(context):
    """التحقق من الرسائل المجدولة وإرسالها"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # البحث عن المستخدمين الذين أكملوا الخطوات ولم يتم إرسال رسالة الإحالة لهم
    c.execute('''SELECT user_id, username, completion_time 
                 FROM users 
                 WHERE completed_steps = TRUE 
                 AND referral_sent = FALSE 
                 AND completion_time IS NOT NULL''')
    
    users = c.fetchall()
    
    for user_id, username, completion_time in users:
        if isinstance(completion_time, str):
            completion_time = datetime.strptime(completion_time, '%Y-%m-%d %H:%M:%S')
        
        time_elapsed = datetime.now() - completion_time
        
        if time_elapsed.total_seconds() >= 24 * 3600:  # 24 ساعة
            try:
                await send_referral_message(context, user_id)
                c.execute("UPDATE users SET referral_sent = TRUE WHERE user_id = ?", (user_id,))
                print(f"✅ تم إرسال رسالة الإحالة للمستخدم {user_id}")
            except Exception as e:
                print(f"❌ خطأ في إرسال رسالة للمستخدم {user_id}: {e}")
    
    conn.commit()
    conn.close()

async def send_referral_message(context, user_id):
    """إرسال رسالة نظام الإحالة"""
    
    # إنشاء رابط الإحالة الفريد
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    referral_message = f"""
    🎊 **تهانينا! حان وقت كسب التوصيات المجانية** 🎊

    ⏰ **لقد مرت 24 ساعة على اكتمال انضمامك - الآن يمكنك بدء كسب المكافآت!**

    📤 **رابط الإحالة الخاص بك:**
    `{referral_link}`

    💰 **مكافآت الإحالة:**
    🎯 **كل صديق يدخل للقناة عبر رابطك = توصية مجانية!**

    📊 **مثال:**
    • 1 صديق = 1 توصية مجانية 📈
    • 3 أصدقاء = 3 توصيات مجانية 💰
    • 10 أصدقاء = 10 توصيات مجانية 🚀

    💡 **طريقة العمل:**
    1. شارك الرابط أعلاه مع أصدقائك
    2. عندما ينضمون للقناة، تحصل على توصية مجانية تلقائياً
    3. استخدم /signal لتحصل على كود التوصية
    4. أرسل الكود إلى {YOUR_ACCOUNT} لاستلام التوصية

    📋 **الأوامر المتاحة:**
    /signal - الحصول على كود توصية
    /mysignals - رؤية التوصيات المتاحة
    /referral - إعادة عرض رابط الإحالة
    """
    
    keyboard = [
        [InlineKeyboardButton("📤 مشاركة الرابط الآن", 
             url=f"https://t.me/share/url?url={referral_link}&text="
                 f"انضم لقناة كاسر الترند واحصل على توصيات تداول مجانية! 🔥%0A%0A"
                 f"كل صديق تجلبه = توصية مجانية! 🎁")],
        [InlineKeyboardButton("🎯 الحصول على كود توصية", callback_data="get_signal_code")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(user_id, referral_message, reply_markup=reply_markup, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"❌ لا يمكن إرسال رسالة للمستخدم {user_id}: {e}")
        return False

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء كود توصية جديد"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT free_signals, username FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result or result[0] <= 0:
        await update.message.reply_text(
            "❌ **لا يوجد لديك توصيات مجانية متاحة**\n\n"
            "💡 **لحصول على توصيات مجانية:**\n"
            "1. شارك رابط الإحالة مع أصدقائك\n"
            "2. كل صديق ينضم للقناة = توصية مجانية\n"
            "3. أرسل /referral لعرض رابطك"
        )
        conn.close()
        return
    
    signal_code = generate_signal_code()
    username = result[1] or "غير معروف"
    
    c.execute("INSERT INTO signal_codes (code, user_id, username) VALUES (?, ?, ?)", 
              (signal_code, user_id, username))
    c.execute("UPDATE users SET free_signals = free_signals - 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    code_message = f"""
    🎯 **كود التوصية الخاص بك**

    🔐 **الكود:** `{signal_code}`
    
    ⚡ **صالح لمدة:** 24 ساعة
    👤 **مخصص ل:** @{username}
    
    📝 **خطوات الاستلام:**
    1. انسخ الكود أعلاه 📋
    2. اذهب إلى {YOUR_ACCOUNT}
    3. أرسل له الكود وسيرد عليك بالتوصية
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{signal_code}")],
        [InlineKeyboardButton("↗️ الذهاب إلى الحساب", url=f"https://t.me/kasraltrnd")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(code_message, reply_markup=reply_markup, parse_mode='Markdown')

async def my_signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض التوصيات المجانية المتاحة"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT free_signals, referrals, completed_steps FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    free_signals = result[0] if result else 0
    referrals = result[1] if result else 0
    completed_steps = result[2] if result else False
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    if not completed_steps:
        message = "❌ **لم تكمل خطوات الانضمام بعد**\n\nاستخدم /start لبدء عملية الانضمام"
    else:
        message = f"""
    🎯 **إحصائياتك:**

    🎁 **التوصيات المجانية المتاحة:** {free_signals}
    👥 **عدد الإحالات الناجحة:** {referrals}

    💰 **كل صديق ينضم للقناة = توصية مجانية!**

    📤 **رابط الإحالة:**
    `{referral_link}`

    💡 **للحصول على توصية:** /signal
    ثم أرسل الكود إلى {YOUR_ACCOUNT}
    """
    
    keyboard = [
        [InlineKeyboardButton("🎯 الحصول على كود توصية", callback_data="get_signal_code")],
        [InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={referral_link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رابط الإحالة فقط"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT completed_steps FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result or not result[0]:
        await update.message.reply_text("❌ **لم تكمل خطوات الانضمام بعد**\n\nاستخدم /start لبدء عملية الانضمام")
        return
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await update.message.reply_text(
        f"📤 **رابط الإحالة الخاص بك:**\n\n`{referral_link}`\n\n"
        f"💡 شارك هذا الرابط مع أصدقائك:\n"
        f"• كل من ينضم للقناة عبر رابطك = توصية مجانية!\n"
        f"• استخدم /signal لتحصل على كود التوصية\n"
        f"• أرسل الكود إلى {YOUR_ACCOUNT} لاستلام التوصية",
        parse_mode='Markdown'
    )

async def verify_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر للتحقق من صحة الكود - للمشرف فقط"""
    user_id = update.effective_user.id
    
    # التحقق إذا كان المستخدم مشرف
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not context.args:
        await update.message.reply_text("⛔ استخدم: /verify <الكود>")
        return
    
    code = context.args[0].upper().strip()
    
    # التحقق من الكود في قاعدة البيانات
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''SELECT sc.code, sc.user_id, sc.username, sc.used, sc.created_time, 
                        u.free_signals, u.referrals
                 FROM signal_codes sc
                 LEFT JOIN users u ON sc.user_id = u.user_id
                 WHERE sc.code = ?''', (code,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text(
            f"❌ **الكود غير صحيح**\n\n"
            f"🔍 الكود: `{code}`\n"
            f"📛 الحالة: ❌ غير موجود في النظام\n\n"
            f"💡 قد يكون الكود:\n"
            f"• من تأليف العميل\n"
            f"• كود قديم منتهي\n"
            f"• خطأ في الكتابة"
        )
        return
    
    code_db, user_id_db, username_db, used, created_time, free_signals, referrals = result
    
    # التحقق إذا كان الكود مستخدم سابقاً
    if used:
        await update.message.reply_text(
            f"⚠️ **الكود مستخدم مسبقاً**\n\n"
            f"🔐 الكود: `{code}`\n"
            f"👤 المستخدم: @{username_db or 'غير معروف'}\n"
            f"🆔 الآيدي: `{user_id_db}`\n"
            f"⏰ وقت الإنشاء: {created_time}\n"
            f"📊 التوصيات المتبقية: {free_signals}\n\n"
            f"❌ **لا يمكن استخدامه مرة أخرى**"
        )
        return
    
    # التحقق إذا انتهت صلاحية الكود (أكثر من 24 ساعة)
    code_time = datetime.strptime(created_time, '%Y-%m-%d %H:%M:%S') if isinstance(created_time, str) else created_time
    if datetime.now() - code_time > timedelta(hours=24):
        await update.message.reply_text(
            f"⏰ **الكود منتهي الصلاحية**\n\n"
            f"🔐 الكود: `{code}`\n"
            f"👤 المستخدم: @{username_db or 'غير معروف'}\n"
            f"🆔 الآيدي: `{user_id_db}`\n"
            f"⏰ وقت الإنشاء: {created_time}\n"
            f"📅 العمر: أكثر من 24 ساعة\n\n"
            f"💡 اطلب من المستخدم استخدام /signal للحصول على كود جديد"
        )
        return
    
    # الكود صحيح وغير مستخدم
    await update.message.reply_text(
        f"✅ **الكود صحيح ومتاح**\n\n"
        f"🔐 الكود: `{code}`\n"
        f"👤 المستخدم: @{username_db or 'غير معروف'}\n"
        f"🆔 الآيدي: `{user_id_db}`\n"
        f"📛 اليوزر: @{username_db or 'لا يوجد'}\n"
        f"📊 التوصيات المتبقية: {free_signals}\n"
        f"👥 إجمالي إحالاته: {referrals}\n"
        f"⏰ وقت الإنشاء: {created_time}\n\n"
        f"🎯 **يمكنك إرسال التوصية له بأمان**\n"
        f"💡 بعد إرسال التوصية، استخدم /use {code} لتسجيله كمستعمل"
    )

async def use_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل الكود كمستعمل - بعد إرسال التوصية"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("⛔ استخدم: /use <الكود>")
        return
    
    code = context.args[0].upper().strip()
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # التحقق من الكود
    c.execute("SELECT code, user_id, username FROM signal_codes WHERE code = ? AND used = FALSE", (code,))
    result = c.fetchone()
    
    if not result:
        await update.message.reply_text(f"❌ الكود غير صحيح أو مستخدم مسبقاً: {code}")
        conn.close()
        return
    
    # تحديث الكود كمستعمل
    c.execute("UPDATE signal_codes SET used = TRUE WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ **تم تسجيل الكود كمستعمل**\n\n"
        f"🔐 الكود: `{code}`\n"
        f"👤 المستخدم: @{result[2] or 'غير معروف'}\n"
        f"🆔 الآيدي: `{result[1]}`\n\n"
        f"📝 تم إرسال التوصية بنجاح"
    )

async def check_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص سريع للكود - نسخة مبسطة"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("⛔ استخدم: /check <الكود>")
        return
    
    code = context.args[0].upper().strip()
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT code, username, used FROM signal_codes WHERE code = ?", (code,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text(f"❌ كود خاطئ: `{code}`")
    elif result[2]:  # if used
        await update.message.reply_text(f"⚠️ كود مستخدم: `{code}`")
    else:
        await update.message.reply_text(f"✅ كود صحيح: `{code}`")

# إضافة دالة للتحقق الدوري من الرسائل المجدولة
async def periodic_check(context):
    """فحص دوري للرسائل المجدولة"""
    await check_pending_referrals(context)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal_command))
    app.add_handler(CommandHandler("mysignals", my_signals_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("verify", verify_code_command))
    app.add_handler(CommandHandler("use", use_code_command))
    app.add_handler(CommandHandler("check", check_code_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_id))
    
    # إضافة فحص دوري كل 30 دقيقة للرسائل المجدولة
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(periodic_check, interval=1800, first=10)  # كل 30 دقيقة
    
    print("🤖 البوت يعمل بنظام 24 ساعة بعد إكمال الخطوات...")
    app.run_polling()

if __name__ == '__main__':
    main()
