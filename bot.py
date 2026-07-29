import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# সার্ভার থেকে টোকেন নেওয়ার জন্য (নিরাপদ উপায়)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ইউজার যখন কোনো মেসেজ বা লিংক দিবে
@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text
    if "http" not in url:
        bot.reply_to(message, "অনুগ্রহ করে একটি সঠিক ভিডিও লিংক দিন (YouTube, Facebook, TikTok, Twitter)।")
        return

    bot.reply_to(message, "🔍 ভিডিওর তথ্য সংগ্রহ করা হচ্ছে... দয়া করে একটু অপেক্ষা করুন।")

    ydl_opts = {'quiet': True, 'noplaylist': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            markup = InlineKeyboardMarkup()
            
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    filesize = f.get('filesize')
                    if filesize:
                        size_in_mb = filesize / (1024 * 1024)
                        resolution = f.get('resolution', 'Unknown Quality')
                        button_text = f"📥 {resolution} ({size_in_mb:.2f} MB)"
                        markup.add(InlineKeyboardButton(button_text, callback_data=f"dl|{f['format_id']}|{url}"))
            
            if len(markup.keyboard) > 0:
                bot.send_message(message.chat.id, "🎬 **নিচের তালিকা থেকে ভিডিওর কোয়ালিটি নির্বাচন করুন:**", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, "দুঃখিত, এই ভিডিওটির সরাসরি সাইজ বা কোয়ালিটি অপশন পাওয়া যায়নি।")
                
    except Exception as e:
        bot.reply_to(message, "⚠️ লিংকটি প্রসেস করতে সমস্যা হচ্ছে।")

# ইউজার যখন বাটনে ক্লিক করবে
@bot.callback_query_handler(func=lambda call: call.data.startswith('dl|'))
def download_video(call):
    data = call.data.split('|')
    format_id = data[1]
    url = data[2]
    
    bot.answer_callback_query(call.id, "ডাউনলোড শুরু হচ্ছে... ⏳")
    bot.edit_message_text("⬇️ আপনার ভিডিওটি ক্লাউডে ডাউনলোড হচ্ছে, একটু সময় দিন...", chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': 'downloaded_video.%(ext)s',
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("📤 টেলিগ্রামে আপলোড করা হচ্ছে...", chat_id=call.message.chat.id, message_id=call.message.message_id)
            
            with open(filename, 'rb') as video_file:
                bot.send_video(call.message.chat.id, video_file, caption="✅ আপনার ভিডিও ডাউনলোড সফল হয়েছে!")
            
            os.remove(filename)
            
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ ভিডিওটি ডাউনলোড বা আপলোড করতে সমস্যা হয়েছে।")

bot.polling()
