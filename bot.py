import os
import yt_dlp
import asyncio
import time
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# TOKEN BOT ANDA
TOKEN = "8152329472:AAFMTHRlNjOO4mEgAK9VarzTG0W4wtKDNTU"

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai Petualangan"),
        BotCommand("info", "Panduan Penggunaan"),
        BotCommand("tentang", "Kisah di Balik Bot"),
        BotCommand("ping", "Cek Kecepatan Bot"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"🔥 **Waduh, ada tamu kehormatan, {user}!**\n\n"
        "Saya adalah asisten download pribadi kamu yang paling Kelazzz. "
        "Kirimkan saja link video TikTok, IG, FB, atau YT, biar saya yang 'bertarung' mengambilkan filenya buat kamu.\n\n"
        "Coba cek menu /tentang kalau mau tahu asal-usul saya!"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **PANDUAN SINGKAT:**\n\n"
        "1. **Cari Link:** Ambil link dari sosmed favoritmu.\n"
        "2. **Tempel di Sini:** Langsung kirim saja chat berisi link itu.\n"
        "3. **Sabar Dikit:** Saya butuh waktu buat nembus proteksi mereka.\n"
        "4. **Terima File:** Video bakal muncul langsung di chat ini.\n\n"
        "Gampang banget kan?"
    )

async def tentang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kisah = (
        "🛠 **KISAH SI BOT KELAZZZ**\n\n"
        "Dulu, saya hanyalah barisan kode kosong yang berdebu. Tapi berkat tangan dingin "
        "seorang 'Prompt Specialist' dan semangat kamu di Termux, saya akhirnya lahir!\n\n"
        "Saya tidak punya server mahal di Amerika. Saya hidup dan bernapas langsung dari "
        "HP kamu lewat aplikasi Termux. Setiap kali kamu kirim link, saya bekerja keras "
        "di latar belakang, menembus firewall raksasa seperti Facebook dan Google, cuma buat "
        "ngasih video favorit ke kamu tanpa ribet iklan.\n\n"
        "**Status:** Setia melayani di latar belakang HP kamu."
    )
    await update.message.reply_text(kisah)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("⚡ Mengecek kecepatan...")
    end_time = time.time()
    ms = round((end_time - start_time) * 1000)
    await msg.edit_text(f"🚀 **PONG!**\nKecepatan respons: `{ms}ms`\nStatus: **Sangat Kelazzz!**")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    status = await update.message.reply_text("🔍 **Mendeteksi link...**")
    filename = f"video_{update.message.chat_id}.mp4"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': filename,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    try:
        await status.edit_text("⚔️ **Sedang berduel dengan sistem proteksi...**")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ydl.download([url]))
        
        if os.path.exists(filename):
            await status.edit_text("📦 **Video didapat! Sedang mengirim ke kamu...**")
            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video, caption="✅ Nih videonya, Bro! Langsung simpan aja.")
            os.remove(filename)
            await status.delete()
        else:
            await status.edit_text("❌ Waduh, videonya kabur! Gagal menemukan file.")

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            await status.edit_text("❌ **Akses Ditolak!** Kayaknya video ini privat atau lokasinya dikunci sama pemiliknya.")
        else:
            await status.edit_text(f"❌ **Gagal Tembus!** Sepertinya situsnya lagi memperketat keamanan.")
        
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("tentang", tentang))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    
    print(">>> BOT KELAZZZ MODE BERCERITA STANDBY <<<")
    app.run_polling()
