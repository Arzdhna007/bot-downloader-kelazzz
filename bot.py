import os, yt_dlp, asyncio, time, http.server, socketserver, threading, sqlite3
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIGURATION =================
TOKEN = "8152329472:AAFMTHRlNjOO4mEgAK9VarzTG0W4wtKDNTU"
ADMIN_ID = 6363297127  # ID Telegram lo
DB_NAME = "bot_data.db"

# Data Payment
PAYMENT_INFO = {
    "dana": "+62895613212076",
    "ovo": "+62895613212076",
    "paypal": "arrizqipramdahana@gmail.com"
}

# ================= PERSENJATAAN KOYEB =================
def run_health_check_server():
    PORT = 80
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f">>> Health Check Server Aktif di Port {PORT} <<<")
        httpd.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

# ================= DATABASE SYSTEM =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, downloads INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT downloads, is_premium FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        res = (0, 0)
    conn.close()
    return res

def update_download_count(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ================= BOT LOGIC =================
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai / Start"),
        BotCommand("bayar", "Aktivasi Sultan / Premium"),
        BotCommand("info", "Panduan / Guide"),
        BotCommand("tentang", "Tentang / About"),
        BotCommand("ping", "Cek Speed"),
        BotCommand("help", "Bantuan / Help"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    downloads, is_prem = get_user_data(user.id)
    lang = user.language_code
    status = "👑 SULTAN" if is_prem else f"🆓 GRATIS ({downloads}/5)"
    
    if lang == 'id':
        msg = (f"🔥 Waduh, ada tamu kehormatan, {user.first_name}!\n\n"
               f"Status Akun: {status}\n"
               "Kirim link video TikTok, IG, FB, atau YT, biar saya bantai download-annya!")
    else:
        msg = (f"🔥 Welcome, {user.first_name}!\n\n"
               f"Account Status: {status}\n"
               "Send any video link from TikTok, IG, FB, or YT, and I'll get it for you!")
    await update.message.reply_text(msg)

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    
    if lang == 'id':
        msg = (f"💎 PAKET SULTAN KELAZZZ 💎\n\n"
               f"Cukup 10k/minggu untuk download Unlimited!\n\n"
               f"💰 Pembayaran:\n"
               f"• DANA/OVO: {PAYMENT_INFO['dana']}\n"
               f"• PayPal: (Hubungi Admin untuk email)\n\n"
               f"📸 Konfirmasi:\n"
               f"Kirim bukti transfer ke Admin.\n"
               f"Sertakan ID kamu: {user_id}")
    else:
        msg = (f"💎 SULTAN KELAZZZ PACKAGE 💎\n\n"
               f"Only 10k/week for Unlimited downloads!\n\n"
               f"💰 Payment:\n"
               f"• DANA/OVO: {PAYMENT_INFO['dana']}\n"
               f"• PayPal: (Contact Admin for email)\n\n"
               f"📸 Confirmation:\n"
               f"Send payment proof to Admin.\n"
               f"Your ID: {user_id}")
    await update.message.reply_text(msg)

async def activate_sultan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ User {target_id} resmi jadi SULTAN!")
        await context.bot.send_message(target_id, "🔥 Selamat! Akun kamu sudah PREMIUM. Enjoy Unlimited Download!")
    except:
        await update.message.reply_text("Format: /sultan [id]")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    downloads, is_prem = get_user_data(user_id)

    if not is_prem and downloads >= 5:
        msg = "❌ Jatah gratis habis! Ketik /bayar untuk jadi Sultan." if lang == 'id' else "❌ Free quota reached! Type /bayar to upgrade."
        await update.message.reply_text(msg)
        return

    url = update.message.text
    if not url.startswith("http"): return

    wait_msg = "🔍 Mendeteksi link..." if lang == 'id' else "🔍 Detecting link..."
    status = await update.message.reply_text(wait_msg)
    filename = f"video_{user_id}_{int(time.time())}.mp4"
    
    try:
        await status.edit_text("⚔️ Processing...")
        ydl_opts = {'format': 'best', 'outtmpl': filename, 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.download([url]))
        
        if os.path.exists(filename):
            await status.edit_text("📦 Sending...")
            caption = "✅ Berhasil Dantai!" if lang == 'id' else "✅ Successfully Bypassed!"
            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video, caption=caption)
            os.remove(filename)
            if not is_prem: update_download_count(user_id)
            await status.delete()
        else:
            await status.edit_text("❌ File not found!")
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)[:50]}")
        if os.path.exists(filename): os.remove(filename)

# Fungsi lain (ping, info, tentang, help) tetap sama...
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("⚡ Checking...")
    ms = round((time.time() - start_time) * 1000)
    await msg.edit_text(f"🚀 PONG! {ms}ms")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bayar", buy_premium))
    app.add_handler(CommandHandler("sultan", activate_sultan))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()