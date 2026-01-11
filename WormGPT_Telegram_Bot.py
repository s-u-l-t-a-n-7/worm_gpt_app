import telebot
import requests
import json

# ====== الإعدادات ======
BOT_TOKEN = '7587800288:AAFe7H7HW57bO8el9mBhz3w74V8qgx-Ql94'  # ضع توكن البوت هنا
ADMIN_IDS = [6118449307]  # ضع ايديك هنا (يمكن إضافة أكثر من ايدي)

# ====== تهيئة البوت ======
bot = telebot.TeleBot(BOT_TOKEN)

# ====== الأوامر الأساسية ======
@bot.message_handler(commands=['start'])
def start_command(message):
    """رسالة الترحيب"""
    welcome_text = """
<b>👋 مرحباً بك في البوت!</b>

<blockquote>⚠️ تنبيه:
هذا البوت تم تطويره للأغراض التعليمية فقط.
المستخدم مسؤول عن كيفية استخدام البوت.</blockquote>

<b>💬 كيف تستخدم البوت؟</b>
فقط أرسل أي سؤال أو استفسار وسأجيبك!

<b>📝 الأوامر المتاحة:</b>
/start - بدء البوت
/help - المساعدة
/about - معلومات عن البوت
"""
    
    try:
        photo_url = 'https://t.me/Z_O_Z_0o0/2'
        bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=welcome_text,
            parse_mode='HTML',
            reply_to_message_id=message.message_id
        )
    except:
        # إذا فشلت الصورة، إرسال النص فقط
        bot.reply_to(message, welcome_text, parse_mode='HTML')


@bot.message_handler(commands=['help'])
def help_command(message):
    """رسالة المساعدة"""
    help_text = """
<b>📖 كيفية استخدام البوت:</b>

1️⃣ أرسل أي سؤال أو استفسار
2️⃣ انتظر الرد من الذكاء الاصطناعي
3️⃣ استمتع بالمحادثة!

<b>💡 أمثلة:</b>
• "ما هي البرمجة؟"
• "اكتب لي كود بايثون"
• "ساعدني في حل هذه المسألة"

<i>البوت يدعم اللغة العربية والإنجليزية</i>
"""
    bot.reply_to(message, help_text, parse_mode='HTML')


@bot.message_handler(commands=['about'])
def about_command(message):
    """معلومات عن البوت"""
    about_text = """
<b>🤖 معلومات عن البوت</b>

<b>📌 الاسم:</b> WormGPT Bot
<b>🔧 التقنية:</b> Telegram Bot API + WormGPT AI
<b>💻 اللغة:</b> Python
<b>📚 المكتبة:</b> pyTelegramBotAPI

<b>✨ الميزات:</b>
• ذكاء اصطناعي متقدم
• دعم الرسائل الطويلة
• واجهة بسيطة وسهلة

<i>تم التطوير بواسطة Python ❤️</i>
"""
    bot.reply_to(message, about_text, parse_mode='HTML')


@bot.message_handler(commands=['stats'])
def stats_command(message):
    """إحصائيات البوت - للأدمن فقط"""
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ هذا الأمر متاح للمطورين فقط")
        return
    
    user_info = f"""
<b>📊 إحصائيات المستخدم:</b>

<b>🆔 الايدي:</b> <code>{message.from_user.id}</code>
<b>👤 الاسم:</b> {message.from_user.first_name}
<b>🔤 اليوزر:</b> @{message.from_user.username if message.from_user.username else 'غير متوفر'}

<i>✅ أنت مطور معتمد</i>
"""
    bot.reply_to(message, user_info, parse_mode='HTML')


# ====== معالج الرسائل النصية ======
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """معالجة جميع الرسائل النصية"""
    user_text = message.text
    
    # إظهار أن البوت يكتب
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # إرسال الطلب للـ AI
        response = requests.post(
            "https://sii3.top/api/error/wormgpt.php",
            data={
                'key': "DarkAI-WormGPT-E487DD2FDAAEDC31A56A8A84",
                'text': user_text
            },
            timeout=30  # تحديد وقت انتظار
        )
        
        # التحقق من نجاح الطلب
        if response.status_code == 200:
            try:
                data = response.json()
                
                if "response" in data:
                    ai_response = data["response"]
                    
                    # التعامل مع الرسائل الطويلة
                    if len(ai_response) > 4000:
                        # تقسيم الرسالة إلى أجزاء
                        for i in range(0, len(ai_response), 4000):
                            bot.send_message(message.chat.id, ai_response[i:i+4000])
                    else:
                        bot.reply_to(message, ai_response)
                else:
                    bot.reply_to(message, "⚠️ عذراً، لم أستطع الحصول على رد من الذكاء الاصطناعي")
                    
            except json.JSONDecodeError:
                bot.reply_to(message, "❌ خطأ في تحليل البيانات من الخادم")
        else:
            bot.reply_to(message, f"⚠️ خطأ في الاتصال بالخادم (كود: {response.status_code})")
            
    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏱️ انتهى وقت الانتظار، حاول مرة أخرى")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "🌐 خطأ في الاتصال بالإنترنت")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ غير متوقع:\n<code>{str(e)}</code>", parse_mode='HTML')
        # إرسال الخطأ للأدمن
        if message.from_user.id in ADMIN_IDS:
            print(f"Error Details: {e}")


# ====== تشغيل البوت ======
if __name__ == '__main__':
    print("🤖 البوت يعمل الآن...")
    print("✅ اضغط Ctrl+C للإيقاف")
    
    try:
        # حذف الـ webhook إذا كان موجود
        bot.delete_webhook()
        # تشغيل البوت
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except KeyboardInterrupt:
        print("\n⛔ تم إيقاف البوت بنجاح")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")