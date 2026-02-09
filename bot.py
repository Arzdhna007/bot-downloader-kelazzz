import os
import yt_dlp
import asyncio
import time
import http.server
import socketserver
import threading
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= PERSENJATAAN KOYEB =================
def run_health_check_server():
    PORT = 80
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f">>> Health Check Server Aktif di Port {PORT} <<<")
        httpd.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()
# ======================================================

TOKEN = "8152329472:AAFMTHRlNjOO4mEgAK9VarzTG0W4wtKDNTU"

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai / Start"),
        BotCommand("info", "Panduan / Guide"),
        BotCommand("tentang", "Tentang / About"),
        BotCommand("ping", "Cek Speed"),
        BotCommand("help", "Bantuan / Help"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code
    
    if lang == 'id':
        msg = (f"🔥 Waduh, ada tamu kehormatan, {user.first_name}!\n\n"
               "Saya adalah asisten download pribadi kamu yang paling Kelazzz. "
               "Kirimkan saja link video TikTok, IG, FB, atau YT, biar saya yang berduel mengambilkan filenya buat kamu.")
    else:
        msg = (f"🔥 Welcome, {user.first_name}!\n\n"
               "I am your premium downloader assistant. "
               "Just send me a video link from TikTok, IG, FB, or YT, and I'll fight to get the file for you.")
    
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code
    if lang == 'id':
        msg = ("🆘 BUTUH BANTUAN?\n\n"
               "Langsung kirim link video saja. Jika error:\n"
               "1. Pastikan video Publik.\n"
               "2. Bukan link Private Group.\n"
               "3. Gunakan link asli (bukan shortlink).")
    else:
        msg = ("🆘 NEED HELP?\n\n"
               "Just send the video link directly. If it fails:\n"
               "1. Make sure the video is Public.\n"
               "2. Not a Private Group link.\n"
               "3. Use the original link (no shortlinks).")
    await update.message.reply_text(msg)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code
    if lang == 'id':
        msg = ("📖 PANDUAN SINGKAT\n\n"
               "1. Cari Link video sosmed.\n"
               "2. Tempel/Kirim di sini.\n"
               "3. Tunggu proses duel proteksi.\n"
               "4. Terima videonya langsung!")
    else:
        msg = ("📖 QUICK GUIDE\n\n"
               "1. Copy the social media link.\n"
               "2. Paste/Send it here.\n"
               "3. Wait for the bypass process.\n"
               "4. Receive your video directly!")
    await update.message.reply_text(msg)

async def tentang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.effective_user.language_code
    if lang == 'id':
        msg = ("🛠 KISAH SI BOT KELAZZZ\n\n"
               "Lahir dari semangat ngoding di Termux, sekarang saya sudah gagah mengudara di Cloud Server Frankfurt! 🇩🇪\n\n"
               "Status: Aktif 24/7 di Cloud.")
    else:
        msg = ("🛠 THE KELAZZZ STORY\n\n"
               "Born from coding passion in Termux, now I am proudly flying on the Cloud Server in Frankfurt! 🇩🇪\n\n"
               "Status: Active 24/7 in the Cloud.")
    await update.message.reply_text(msg)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("⚡ Checking speed...")
    ms = round((time.time() - start_time) * 1000)
    await msg.edit_text(f"🚀 PONG!\nSpeed: {ms}ms\nStatus: Very Kelazzz!")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    lang = update.effective_user.language_code
    if not url.startswith("http"):
        return

    wait_msg = "🔍 Mendeteksi link..." if lang == 'id' else "🔍 Detecting link..."
    status = await update.message.reply_text(wait_msg)
    filename = f"video_{update.message.chat_id}_{int(time.time())}.mp4"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': filename,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    try:
        duel_msg = "⚔️ Sedang berduel dengan proteksi..." if lang == 'id' else "⚔️ Fighting the protection system..."
        await status.edit_text(duel_msg)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ydl.download([url]))
        
        if os.path.exists(filename):
            send_msg = "📦 Video didapat! Mengirim..." if lang == 'id' else "📦 Video captured! Sending..."
            await status.edit_text(send_msg)
            
            caption = "✅ Nih videonya, Bro!" if lang == 'id' else "✅ Here is your video!"
            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video, caption=caption)
            
            os.remove(filename)
            await status.delete()
        else:
            fail_msg = "❌ Videonya kabur!" if lang == 'id' else "❌ Video escaped!"
            await status.edit_text(fail_msg)

    except Exception as e:
        print(f"Error: {e}")
        error_text = "❌ Gagal Tembus!" if lang == 'id' else "❌ Bypass Failed!"
        await status.edit_text(error_text)
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("tentang", tentang))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    
    print(">>> BOT ULTIMATE MULTI-LANGUAGE STANDBY <<<")
    app.run_polling()