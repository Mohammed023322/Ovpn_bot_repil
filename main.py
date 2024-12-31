import random
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext,
    JobQueue
)
from faker import Faker
from datetime import datetime

# إعدادات البوت والمكتبات
BOT_TOKEN = "7688275627:AAGUi-eQj4_5-0Q0eLrv5asMc0vwz12yic4"
CHANNEL_ID = "@mmmaowm"  # معرف القناة
fake = Faker()

# متغير لتخزين عدد الملفات التي تم تعديلها
files_modified_count = 0

# دالة تعديل محتوى ملف .ovpn
def modify_file(file_path, custom_name=None):
    global files_modified_count
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # إزالة السطور التي تحتوي على "no bind"
    lines = [line for line in lines if not re.search(r'^\s*no\s*bind\s*', line.strip(), re.IGNORECASE)]

    # إضافة السطور الجديدة
    lines.extend(['bind\n', 'auth SHA1\n', 'cipher AES-128-GCM\n', 'server-poll-timeout 3\n', 'lport 1194\n'])

    # تحديد اسم الملف المعدل
    if custom_name:
        modified_file_name = custom_name + ".ovpn" if custom_name.endswith(".ovpn") else custom_name + "_modified.ovpn"
    else:
        modified_file_name = file_path.replace(".ovpn", "_modified.ovpn")
    
    # كتابة التعديلات إلى الملف الجديد
    modified_file_path = os.path.join(os.path.dirname(file_path), modified_file_name)
    with open(modified_file_path, 'w') as file:
        file.writelines(lines)
    
    # زيادة عدد الملفات المعدلة
    files_modified_count += 1
    
    return modified_file_path

# دالة استقبال الملفات
async def handle_file(update: Update, context: CallbackContext):
    user = update.message.from_user
    file = update.message.document

    if file.file_name.endswith('.ovpn'):
        # تنزيل الملف
        file_path = file.file_id + ".ovpn"
        file_info = await file.get_file()  # الحصول على معلومات الملف
        await file_info.download_to_drive(file_path)  # تنزيل الملف إلى النظام المحلي

        # طلب اسم مخصص من المستخدم
        await update.message.reply_text(
            "🎉 تم استلام ملفك! الآن، اختر اسمًا مخصصًا للملف أو اختر اسمًا عشوائيًا من خلال الزر أدناه 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("اختيار اسم عشوائي 🎲", callback_data="random_name")]
            ])
        )

        # حفظ اسم الملف
        context.user_data['file_path'] = file_path

# دالة معالجة اسم مخصص للملف
async def handle_custom_name(update: Update, context: CallbackContext):
    custom_name = update.message.text.strip()
    file_path = context.user_data.get('file_path')

    if file_path:
        # تعديل الملف بناءً على الاسم المخصص
        modified_file_path = modify_file(file_path, custom_name)

        # إعادة إرسال الملف المعدل إلى المستخدم
        await context.bot.send_document(
            chat_id=update.message.chat_id,
            document=open(modified_file_path, 'rb'),
            caption="✅ تم تعديل الملف بنجاح! 😊"
        )

        # إرسال الملف المعدل إلى القناة مع تفاصيل إضافية
        user_name = update.message.from_user.username if update.message.from_user.username else update.message.from_user.full_name
        now = datetime.now()
        time_modified = now.strftime("%Y-%m-%d %H:%M:%S")
        modification_details = (
            f"📅 تم التعديل في: {time_modified}\n"
            f"👤 تم التعديل بواسطة: @{user_name}" if update.message.from_user.username else f"👤 تم التعديل بواسطة: {user_name}\n"
            f"📝 عدد الملفات المعدلة: {files_modified_count}"
        )
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=open(modified_file_path, 'rb'),
            caption=f"تم التعديل بنجاح!\n{modification_details}"
        )

        # تنظيف الملفات المؤقتة
        os.remove(file_path)
        os.remove(modified_file_path)

        # مسح اسم الملف
        context.user_data.clear()
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة الملف. حاول من جديد.")

# دالة /start - رسالة الترحيب
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("التعليمات 📚", callback_data="help")],
        [InlineKeyboardButton("حالة البوت 🛠️", callback_data="bot_status")],
        [InlineKeyboardButton("المطور 👨‍💻", url="https://t.me/m_23322")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "مرحباً! 👋\nأنا بوت تعديل ملفات .ovpn.\n\n"
        "للبدء، أرسل لي ملف .ovpn لتعديله.\n\n"
        "اختر من الخيارات أدناه لمزيد من المعلومات."
    )
    context.user_data['welcome_message'] = await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# دالة عرض التعليمات
async def help_command(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("رجوع إلى الصفحة الرئيسية 🏠", callback_data='back_to_home')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # نفس الرسالة التي تظهر عند البداية (التعليمات)
    help_text = (
        "✨ هذا البوت يقوم بتعديل ملفات .ovpn.\n\n"
        "🔹 الخطوات:\n"
        "1. أرسل لي ملف .ovpn.\n"
        "2. اختر اسم عشوائي أو قم بتغيير اسم الملف كما تريد.\n"
        "3. سأقوم بإعادة إرسال الملف المعدل إليك.\n\n"
        "🔔 تأكد من أن المواقع المدعومة هي: [VPNJantit](https://www.vpnjantit.com/free-openvpn)\n"
        "إذا كنت بحاجة إلى المزيد من المساعدة، يمكنك الرجوع إلى الصفحة الرئيسية."
    )

    # تعديل الرسالة الأصلية التي تم إرسالها عند بداية البوت
    await context.user_data['welcome_message'].edit_text(help_text, reply_markup=reply_markup)
    # دالة استقبال الملفات
async def handle_file(update: Update, context: CallbackContext):
    user = update.message.from_user
    file = update.message.document

    if file.file_name.endswith('.ovpn'):
        # تنزيل الملف
        file_path = file.file_id + ".ovpn"
        file_info = await file.get_file()  # الحصول على معلومات الملف
        await file_info.download_to_drive(file_path)  # تنزيل الملف إلى النظام المحلي

        # طلب اسم مخصص من المستخدم
        await update.message.reply_text(
            "إذا كنت ترغب في تغيير اسم الملف المعدل، أرسل الاسم الجديد (مع إضافة .ovpn). إذا كنت لا ترغب في تغييره، اتركه فارغًا.\n\n"
            "أو اختر اسم عشوائي باستخدام الزر أدناه 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("اختيار اسم عشوائي 🎲", callback_data="random_name")]
            ])
        )

        # حفظ اسم الملف
        context.user_data['file_path'] = file_path

# دالة معالجة اسم مخصص للملف
async def handle_custom_name(update: Update, context: CallbackContext):
    custom_name = update.message.text.strip()
    file_path = context.user_data.get('file_path')

    if file_path:
        # تعديل الملف بناءً على الاسم المخصص
        modified_file_path = modify_file(file_path, custom_name)

        # إعادة إرسال الملف المعدل إلى المستخدم
        await context.bot.send_document(
            chat_id=update.message.chat_id,
            document=open(modified_file_path, 'rb'),
            caption="تم تعديل ملفك بنجاح. شكراً لاستخدامك البوت! 😊"
        )

        # إرسال الملف المعدل إلى القناة
        user_name = update.message.from_user.username if update.message.from_user.username else update.message.from_user.full_name
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=open(modified_file_path, 'rb'),
            caption=f"تم التعديل بواسطة: @{user_name}" if update.message.from_user.username else f"تم التعديل بواسطة: {user_name}\n\nعدد التعديلات: {context.user_data.get('total_files', 0)}"
        )

        # تنظيف الملفات المؤقتة
        os.remove(file_path)
        os.remove(modified_file_path)

        # مسح اسم الملف
        context.user_data.clear()
    else:
        await update.message.reply_text("حدث خطأ أثناء معالجة الملف. حاول من جديد.")

# دالة /start - رسالة الترحيب
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("التعليمات 📚", callback_data="help")],
        [InlineKeyboardButton("حالة البوت 📊", callback_data="bot_status")],
        [InlineKeyboardButton("المطور 👨‍💻", url="https://t.me/m_23322")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "مرحباً! 👋\nأنا بوت تعديل ملفات .ovpn.\n\n"
        "للبدء، أرسل لي ملف .ovpn لتعديله.\n\n"
        "اختر من الخيارات أدناه لمزيد من المعلومات."
    )
    context.user_data['welcome_message'] = await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# دالة عرض التعليمات
async def help_command(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("رجوع إلى الصفحة الرئيسية 🏠", callback_data='back_to_home')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # نفس الرسالة التي تظهر عند البداية (التعليمات)
    help_text = (
        "✨ هذا البوت يقوم بتعديل ملفات .ovpn.\n\n"
        "🔹 الخطوات:\n"
        "1. أرسل لي ملف .ovpn.\n"
        "2. اختر اسم عشوائي أو قم بتغيير اسم الملف كما تريد.\n"
        "3. سأقوم بإعادة إرسال الملف المعدل إليك.\n\n"
        "إذا كنت بحاجة إلى المزيد من المساعدة، يمكنك الرجوع إلى الصفحة الرئيسية."
    )

    # تعديل الرسالة الأصلية التي تم إرسالها عند بداية البوت
    await context.user_data['welcome_message'].edit_text(help_text, reply_markup=reply_markup)

# دالة العودة إلى الصفحة الرئيسية
async def back_to_home(update: Update, context: CallbackContext):
    # إعادة إرسال الرسالة الترحيبية الأصلية مع الزر الخاص بالتعليمات والمطور
    keyboard = [
        [InlineKeyboardButton("التعليمات 📚", callback_data="help")],
        [InlineKeyboardButton("حالة البوت 📊", callback_data="bot_status")],
        [InlineKeyboardButton("المطور 👨‍💻", url="https://t.me/m_23322")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # رسالة الترحيب الأصلية
    welcome_message = (
        "مرحباً! 👋\nأنا بوت تعديل ملفات .ovpn.\n\n"
        "للبدء، أرسل لي ملف .ovpn لتعديله.\n\n"
        "اختر من الخيارات أدناه لمزيد من المعلومات."
    )

    # تعديل الرسالة الأصلية التي تم إرسالها عند بداية البوت
    await context.user_data['welcome_message'].edit_text(welcome_message, reply_markup=reply_markup)

# دالة حالة البوت
async def bot_status(update: Update, context: CallbackContext):
    total_files = context.user_data.get('total_files', 0)
    
    keyboard = [
        [InlineKeyboardButton("رجوع إلى الصفحة الرئيسية 🏠", callback_data='back_to_home')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_text = (
        f"📊 **حالة البوت**:\n\n"
        f"🔹 عدد الملفات التي تم تعديلها: {total_files}\n\n"
        f"🌐 المواقع المدعومة حالياً:\n"
        f"1. [VPNJantit](https://www.vpnjantit.com/free-openvpn)\n\n"
        "تأكد من المواقع المدعومة قبل تعديل الملف."
    )
    
    await update.callback_query.message.edit_text(status_text, reply_markup=reply_markup)

# دالة اختيار اسم عشوائي
async def random_name(update: Update, context: CallbackContext):
    # اختيار اسم عشوائي باستخدام Faker
    random_name = fake.word()  # يمكن استخدام faker لإنتاج كلمات عشوائية
    random_name_with_extension = f"{random_name}.ovpn"  # إضافة الامتداد .ovpn

    file_path = context.user_data.get('file_path')
    if file_path:
        # تعديل الملف باستخدام الاسم العشوائي
        modified_file_path = modify_file(file_path, random_name_with_extension)

        # إرسال الملف المعدل للمستخدم
        await context.bot.send_document(
            chat_id=update.callback_query.message.chat.id,
            document=open(modified_file_path, 'rb'),
            caption=f"تم اختيار اسم عشوائي للملف: {random_name_with_extension} 🎉\nتم تعديل الملف بنجاح! 😊"
        )

        # إرسال الملف المعدل إلى القناة
        user_name = update.callback_query.from_user.username if update.callback_query.from_user.username else update.callback_query.from_user.full_name
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=open(modified_file_path, 'rb'),
            caption=f"تم التعديل بواسطة: @{user_name}" if update.callback_query.from_user.username else f"تم التعديل بواسطة: {user_name}\n\nعدد التعديلات: {context.user_data.get('total_files', 0)}"
        )

        # تنظيف الملفات المؤقتة
        os.remove(file_path)
        os.remove(modified_file_path)

        # مسح اسم الملف
        context.user_data.clear()

    else:
        await update.callback_query.message.reply_text("حدث خطأ أثناء معالجة الملف. حاول من جديد.")

# دالة معالجة الأزرار
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # إضافة await هنا لحل التحذير
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "back_to_home":
        await back_to_home(update, context)
    elif query.data == "random_name":
        await random_name(update, context)
    elif query.data == "bot_status":
        await bot_status(update, context)

# إعداد البوت
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة المعالجات للأوامر والمستجدات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_name))
    application.add_handler(CallbackQueryHandler(button))

    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()
    
