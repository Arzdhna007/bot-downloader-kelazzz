import os, yt_dlp, asyncio, time, sqlite3, threading
from flask import Flask, request, jsonify
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIGURATION =================
TOKEN = "8152329472:AAFMTHRlNjOO4mEgAK9VarzTG0W4wtKDNTU"
ADMIN_ID = 6363297127  # ID Telegram lo
DB_NAME = "bot_data.db"
TRAKTEER_LINK = "https://trakteer.id/arrizqipram" # Username Trakteer lo

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

def activate_premium_db(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ================= WEBHOOK SERVER (FLASK) =================
server = Flask(__name__)

@server.route('/webhook', methods=['POST'])
def trakteer_webhook():
    data = request.json
    try:
        # Trakteer mengirim pesan di field 'supporter_message'
        msg = data.get('supporter_message', '')
        # Ambil angka ID saja dari pesan dukungan
        user_id = int(''.join(filter(str.isdigit, msg)))
        activate_premium_db(user_id)
        print(f">>> [AUTO SULTAN] ID {user_id} TELAH AKTIF! <<<")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook Error: {e}")
        # Tetap balas 200 agar Trakteer tidak terus-menerus mencoba ulang (retry)
        return jsonify({"status": "ignored"}), 200

def run_server():
    # Koyeb mewajibkan port 80 untuk Public URL
    server.run(host='0.0.0.0', port=80)

# ================= BOT LOGIC =================
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai / Start"),
        BotCommand("bayar", "Aktivasi Sultan / Premium"),
        BotCommand("ping", "Cek Speed"),
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
               "Kirim link video TikTok, IG, FB, atau YT untuk bantai!")
    else:
        msg = (f"🔥 Welcome, {user.first_name}!\n\n"
               f"Account Status: {status}\n"
               "Send any video link from TikTok, IG, FB, or YT!")
    await update.message.reply_text(msg)

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    
    if lang == 'id':
        msg = (f"💎 PAKET SULTAN OTOMATIS 💎\n\n"
               f"1. Klik link: {TRAKTEER_LINK}\n"
               f"2. Bayar Rp10.000 (1 Cendol).\n"
               f"3. WAJIB: Tulis ID kamu di pesan dukungan: `{user_id}`\n\n"
               "Status Sultan aktif otomatis setelah bayar!")
    else:
        msg = (f"💎 AUTOMATIC SULTAN PACKAGE 💎\n\n"
               f"1. Visit: {TRAKTEER_LINK}\n"
               f"2. Pay Rp10.000 (1 Unit).\n"
               f"3. REQUIRED: Write your ID in the message: `{user_id}`\n\n"
               "Sultan status will activate automatically!")
    await update.message.reply_text(msg, parse_mode="Markdown")

async def activate_sultan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        activate_premium_db(target_id)
        await update.message.reply_text(f"✅ User {target_id} resmi jadi SULTAN!")
        await context.bot.send_message(target_id, "🔥 Akun kamu sudah PREMIUM. Unlimited Download!")
    except:
        await update.message.reply_text("Format: /sultan [id]")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    downloads, is_prem = get_user_data(user_id)

    if not is_prem and downloads >= 5:
        msg = "❌ Jatah habis! Ketik /bayar untuk jadi Sultan." if lang == 'id' else "❌ Quota reached! Type /bayar."
        await update.message.reply_text(msg)
        return

    url = update.message.text
    if not url.startswith("http"): return

    wait_msg = "🔍 Mendeteksi link..." if lang == 'id' else "🔍 Detecting..."
    status = await update.message.reply_text(wait_msg)
    filename = f"video_{user_id}_{int(time.time())}.mp4"
    
    try:
        await status.edit_text("⚔️ Processing...")
        ydl_opts = {'format': 'best', 'outtmpl': filename, 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.download([url]))
        
        if os.path.exists(filename):
            await status.edit_text("📦 Sending...")
            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video, caption="✅ Berhasil Dantai!")
            os.remove(filename)
            if not is_prem: update_download_count(user_id)
            await status.delete()
        else:
            await status.edit_text("❌ File not found!")
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)[:50]}")
        if os.path.exists(filename): os.remove(filename)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("⚡ Checking...")
    ms = round((time.time() - start_time) * 1000)
    await msg.edit_text(f"🚀 PONG! {ms}ms")

if __name__ == '__main__':
    # Jalankan Webhook di background
    threading.Thread(target=run_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bayar", buy_premium))
    app.add_handler(CommandHandler("sultan", activate_sultan))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    
    print(">>> BOT & WEBHOOK TRAKTEER SIAP BANTAI <<<")
    app.run_polling()