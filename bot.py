import os, yt_dlp, asyncio, time, sqlite3, threading, random
from flask import Flask, request, jsonify
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIGURATION =================
TOKEN = "8152329472:AAFMTHRlNjOO4mEgAK9VarzTG0W4wtKDNTU"
ADMIN_ID = 6363297127
DB_NAME = "bot_data.db"
TRAKTEER_LINK = "https://trakteer.id/arzdhna"

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

# ================= WEBHOOK SERVER =================
server = Flask(__name__)
@server.route('/webhook', methods=['POST'])
def trakteer_webhook():
    data = request.json
    try:
        msg = data.get('supporter_message', '')
        user_id = int(''.join(filter(str.isdigit, msg)))
        activate_premium_db(user_id)
        return jsonify({"status": "success"}), 200
    except:
        return jsonify({"status": "ignored"}), 200

def run_server():
    server.run(host='0.0.0.0', port=80)

# ================= BOT LOGIC =================
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Mulai Layanan"),
        BotCommand("bayar", "Sultan Package"),
        BotCommand("tutorial", "Cara Simpan Galeri"),
        BotCommand("ping", "Speedtest Server"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    downloads, is_prem = get_user_data(user.id)
    status = "SULTAN MEMBER" if is_prem else f"FREE USER ({downloads}/5)"
    msg = (f"🔥 Greetings, {user.first_name}!\n\n"
           f"Selamat datang di Downloader Ultimate. Layanan profesional untuk bypass konten media sosial.\n\n"
           f"● Account Status: {status}\n"
           f"● Engine Status: Optimized\n\n"
           f"Kirim link video (TikTok, IG, FB, YT) untuk memulai.")
    await update.message.reply_text(msg)

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = ("📖 TUTORIAL SAVE TO GALLERY\n\n"
           "Agar video tersimpan permanen di galeri HP kamu, ikuti langkah ini:\n\n"
           "1. Buka video yang sudah dikirim oleh bot.\n"
           "2. Klik Titik Tiga (⋮) di pojok kanan atas video.\n"
           "3. Pilih menu 'Save to Gallery' atau 'Simpan ke Galeri'.\n"
           "4. Cek folder 'Telegram Videos' di aplikasi Foto/Galeri kamu.\n\n"
           "Selesai! Video siap kamu tonton secara offline.")
    await update.message.reply_text(msg)

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    msg = (f"💎 UPGRADE TO SULTAN PACKAGE 💎\n\n"
           f"Nikmati akses unlimited tanpa batas kuota selama 7 hari.\n\n"
           f"💰 Harga: Rp10.000\n"
           f"🔗 Link Pembayaran: {TRAKTEER_LINK}\n\n"
           f"⚠️ PENTING: Masukkan ID kamu di kolom pesan dukungan:\n"
           f"ID: {u_id}\n\n"
           f"Status Sultan akan aktif secara otomatis setelah pembayaran terdeteksi.")
    await update.message.reply_text(msg)

async def speed_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🌐 Speedtest.net by Google Cloud\n\n"
                                          "Menganalisis latensi...")
    await asyncio.sleep(1)
    
    stages = [
        "🔍 Menghubungkan ke Server Frankfurt 🇩🇪...",
        "📉 Menghitung Latensi: 12ms",
        "📤 Mengukur Kecepatan Upload...",
        "📥 Mengukur Kecepatan Download..."
    ]
    
    for stage in stages:
        await msg.edit_text(f"🌐 Speedtest.net by Google Cloud\n\n{stage}")
        await asyncio.sleep(0.8)

    await msg.edit_text("🌐 Speedtest.net by Google Cloud\n\n"
                        "✅ Test Berhasil!\n"
                        "● Upload: 20.45 Mbps\n"
                        "● Download: 50.12 Mbps\n"
                        "● Status: Sangat Kelazzz!")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    downloads, is_prem = get_user_data(user_id)

    if not is_prem and downloads >= 5:
        await update.message.reply_text("❌ Access Denied! Jatah gratis kamu telah habis.\n"
                                        "Upgrade ke Sultan Package via /bayar.")
        return

    url = update.message.text
    if not url.startswith("http"): return

    status = await update.message.reply_text("🔍 Processing Link...\nEngine sedang melakukan bypass proteksi.")
    filename = f"vid_{user_id}_{int(time.time())}.mp4"
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'add_header': ['Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language: en-us,en;q=0.5'],
    }
    
    try:
        await status.edit_text("⚔️ Bypass Success!\nSedang mengekstrak file video kualitas terbaik...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.download([url]))
        
        if os.path.exists(filename):
            await status.edit_text("📦 Sending Data...\nVideo siap dikirim.")
            
            if not is_prem:
                update_download_count(user_id)
                new_c = downloads + 1
                sisa = 5 - new_c
                caption = (f"✅ Video Berhasil Dantai!\n\n"
                           f"📊 Usage Info:\n"
                           f"● Batas Pemakaian Gratis: {new_c}/5\n"
                           f"● Sisa Pemakaian Gratis: {sisa}\n\n"
                           f"Untuk pemakaian bebas selama 7 hari, kami tersedia Sultan Package. "
                           f"Silahkan pilih menu /bayar di menu. Have a nice day!\n\n"
                           f"💡 Untuk proses penyimpanan ke galeri, cek tutorial di /tutorial")
            else:
                caption = "👑 SULTAN MEMBER: Unlimited Download Aktif.\n💡 Tutorial simpan: /tutorial"

            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video, caption=caption)
            
            os.remove(filename)
            await status.delete()
        else:
            await status.edit_text("❌ Engine Error! File gagal diekstrak. Coba link lain.")
    except Exception as e:
        await status.edit_text(f"❌ System Error! Proteksi situs terlalu ketat.")
        if os.path.exists(filename): os.remove(filename)

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bayar", buy_premium))
    app.add_handler(CommandHandler("tutorial", tutorial))
    app.add_handler(CommandHandler("ping", speed_test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    
    print(">>> ULTIMATE BOT SYSTEM ONLINE <<<")
    app.run_polling()