from __future__ import annotations
import os
import time
import json
import asyncio
import logging
import smtplib
import subprocess
import signal
import sys
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, Set, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG EMAIL ROTATION ----------------
EMAIL_ACCOUNTS = [
    {
        "email": "apalahhahaha910@gmail.com",
        "app_password": "e r m j f l c q p w o i p p g j",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "wildanjayasopianwilda@gmail.com",
        "app_password": "nreq lmkm cnor xjhd", 
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "cukaishee@gmail.com",
        "app_password": "qfyx wjmb kqfz bnjn",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    },
    {
        "email": "contoh@gmail.com",
        "app_password": "AppPaswword",
        "sent_count": 0,
        "max_per_account": 32
    }
]

TO_EMAIL = "support@support.whatsapp.com"
CURRENT_EMAIL_INDEX = 0
EMAIL_STATS_FILE = "email_stats.json"

# ---------------- BOT CONFIG ----------------
BOT_TOKEN = "8535206102:AAHP2CEgPzcmOTi4gNljU8649xlEyxvQ9sI"
OWNER_ID = 1255764950

SEND_COOLDOWN_SECONDS = 5 * 60
REQUEST_COOLDOWN_SECONDS = 60
NOTIFY_OWNER_ON_SEND = True
BC_DELAY_SECONDS = 0.5

# persistence files
ALLOWED_FILE = "allowed_users.txt"
STATS_FILE = "stats.txt"
CONFIG_FILE = "config.json"

# UI / cosmetic
NEON_BORDER = "═" * 42
PROGRESS_STEPS = 8
ANIM_DELAY = 0.12

# ---------------- logging ----------------
logging.basicConfig(
    format="\033[95m⚡[Kayzii New Eraa]\033[0m %(asctime)s — %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("Kayzii New Eraa")

# ---------------- runtime state ----------------
BOT_START_TIME: datetime = None
allowed_users: Set[int] = set()
pending_requests: Set[int] = set()
request_cooldowns: Dict[int, float] = {}
user_last_send: Dict[int, float] = {}
stats = {"sent": 0, "failed": 0, "users": set(), "numbers": set(), "user_counts": {}}

# extra runtime
registered_chats: Set[int] = set()
BOT_MODE = "chat"
_config_lock = asyncio.Lock()

# ---------------- 24 HOUR SYSTEM FIXES ----------------
RUN_24H_FILE = "bot_24h_enabled"
BOT_24H_PID_FILE = "bot_24h.pid"
RESTART_SCRIPT = "restart_24h.sh"
BOT_24H_LOG = "bot_24h.log"

def is_24h_enabled() -> bool:
    """Check if 24h mode is enabled"""
    return os.path.exists(RUN_24H_FILE)

def enable_24h() -> bool:
    """Enable 24h mode"""
    try:
        with open(RUN_24H_FILE, "w") as f:
            f.write("enabled")
        logger.info("✅ Fitur 24 jam diaktifkan")
        
        # Create restart script
        create_restart_script()
        return True
    except Exception as e:
        logger.error(f"❌ Gagal mengaktifkan fitur 24 jam: {e}")
        return False

def disable_24h() -> bool:
    """Disable 24h mode and stop background process"""
    try:
        # Stop any running 24h process
        stop_24h_process()
        
        if os.path.exists(RUN_24H_FILE):
            os.remove(RUN_24H_FILE)
        logger.info("✅ Fitur 24 jam dinonaktifkan")
        return True
    except Exception as e:
        logger.error(f"❌ Gagal menonaktifkan fitur 24 jam: {e}")
        return False

def create_restart_script():
    """Create the restart script for 24h mode"""
    script_content = """#!/bin/bash
# Bot 24h Restart Script
# Created by WhatsApp Appeal Bot

echo "🚀 Starting WhatsApp Appeal Bot in 24h mode..."
echo "📅 Started at: $(date)"

BOT_PID_FILE="bot_24h.pid"
LOG_FILE="bot_24h.log"
ENABLE_FILE="bot_24h_enabled"

# Function to stop existing bot
stop_bot() {
    if [ -f "$BOT_PID_FILE" ]; then
        OLD_PID=$(cat "$BOT_PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "🛑 Stopping existing bot (PID: $OLD_PID)..."
            kill "$OLD_PID"
            sleep 3
            # Force kill if still running
            if kill -0 "$OLD_PID" 2>/dev/null; then
                kill -9 "$OLD_PID"
            fi
        fi
        rm -f "$BOT_PID_FILE"
    fi
    # Also kill any python processes from this bot
    pkill -f "python.*a.py" 2>/dev/null || true
}

# Function to check if 24h mode is still enabled
is_24h_enabled() {
    [ -f "$ENABLE_FILE" ]
}

# Cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    stop_bot
    exit 0
}

# Set trap for signals
trap cleanup SIGINT SIGTERM

# Main loop
while is_24h_enabled; do
    echo "🔁 Restarting bot... $(date)"
    stop_bot
    
    # Start bot in background
    echo "🤖 Starting bot process..."
    python3 a.py >> "$LOG_FILE" 2>&1 &
    BOT_PID=$!
    
    # Save PID
    echo $BOT_PID > "$BOT_PID_FILE"
    echo "✅ Bot started with PID: $BOT_PID"
    
    # Wait for bot process to finish
    wait $BOT_PID
    EXIT_CODE=$?
    
    echo "⚠️ Bot stopped with exit code: $EXIT_CODE at $(date)"
    
    # Check if 24h mode is still enabled
    if ! is_24h_enabled; then
        echo "⏰ 24h mode disabled, stopping..."
        stop_bot
        break
    fi
    
    echo "🔄 Restarting in 5 seconds..."
    sleep 5
done

echo "✅ 24h mode stopped at $(date)"
"""
    
    try:
        with open(RESTART_SCRIPT, "w") as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(RESTART_SCRIPT, 0o755)
        logger.info(f"✅ Created restart script: {RESTART_SCRIPT}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create restart script: {e}")
        return False

def stop_24h_process():
    """Stop any running 24h process"""
    try:
        # Stop restart script first
        subprocess.run(["pkill", "-f", RESTART_SCRIPT], capture_output=True)
        subprocess.run(["pkill", "-f", "restart_24h.sh"], capture_output=True)
        
        # Stop bot process
        if os.path.exists(BOT_24H_PID_FILE):
            with open(BOT_24H_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"✅ Stopped bot process (PID: {pid})")
                time.sleep(2)
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
            except ProcessLookupError:
                logger.info("ℹ️ Bot process already stopped")
            except Exception as e:
                logger.warning(f"⚠️ Could not stop bot process: {e}")
            
            # Remove PID file
            if os.path.exists(BOT_24H_PID_FILE):
                os.remove(BOT_24H_PID_FILE)
                
        # Kill any remaining python processes
        subprocess.run(["pkill", "-f", "python.*a.py"], capture_output=True)
        
    except Exception as e:
        logger.warning(f"⚠️ Error stopping 24h process: {e}")

def start_24h_process() -> Tuple[bool, str]:
    """Start the 24h process manually"""
    try:
        if not is_24h_enabled():
            return False, "Mode 24 jam belum diaktifkan"
        
        if not os.path.exists(RESTART_SCRIPT):
            create_restart_script()
            if not os.path.exists(RESTART_SCRIPT):
                return False, "Script restart tidak ditemukan"
        
        # Stop any existing process first
        stop_24h_process()
        
        # Start new process
        process = subprocess.Popen(
            [f"./{RESTART_SCRIPT}"],
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        logger.info(f"✅ Started 24h process with PID: {process.pid}")
        return True, f"Process started with PID: {process.pid}"
        
    except Exception as e:
        logger.error(f"❌ Failed to start 24h process: {e}")
        return False, f"Gagal memulai: {str(e)}"

def get_24h_status() -> Dict[str, str]:
    """Get detailed 24h mode status"""
    status = {
        "enabled": is_24h_enabled(),
        "script_exists": os.path.exists(RESTART_SCRIPT),
        "pid_file_exists": os.path.exists(BOT_24H_PID_FILE),
        "process_running": False,
        "restart_script_running": False,
        "pid": None
    }
    
    # Check if restart script is running
    try:
        result = subprocess.run(
            ["pgrep", "-f", RESTART_SCRIPT],
            capture_output=True,
            text=True
        )
        status["restart_script_running"] = bool(result.stdout.strip())
    except:
        pass
    
    # Check if bot process is running
    if status["pid_file_exists"]:
        try:
            with open(BOT_24H_PID_FILE, "r") as f:
                pid = int(f.read().strip())
                status["pid"] = pid
                
                # Check if process is running
                try:
                    os.kill(pid, 0)  # Check if process exists
                    status["process_running"] = True
                except (ProcessLookupError, OSError):
                    status["process_running"] = False
        except Exception as e:
            logger.warning(f"Error reading PID file: {e}")
    
    return status

# ---------------- Email Rotation System ----------------
def load_email_stats():
    """Load email statistics from file"""
    global EMAIL_ACCOUNTS, CURRENT_EMAIL_INDEX
    if os.path.exists(EMAIL_STATS_FILE):
        try:
            with open(EMAIL_STATS_FILE, "r") as f:
                data = json.load(f)
                for i, account in enumerate(EMAIL_ACCOUNTS):
                    if i < len(data.get("accounts", [])):
                        EMAIL_ACCOUNTS[i]["sent_count"] = data["accounts"][i].get("sent_count", 0)
                CURRENT_EMAIL_INDEX = data.get("current_index", 0)
            logger.info("✅ Email stats loaded")
        except Exception as e:
            logger.warning("Failed loading email stats: %s", e)

def save_email_stats():
    """Save email statistics to file"""
    try:
        data = {
            "accounts": [
                {"sent_count": account["sent_count"]} 
                for account in EMAIL_ACCOUNTS
            ],
            "current_index": CURRENT_EMAIL_INDEX
        }
        with open(EMAIL_STATS_FILE, "w") as f:
            json.dump(data, f)
        logger.info("💾 Email stats saved")
    except Exception as e:
        logger.warning("Failed saving email stats: %s", e)

def get_current_email() -> dict:
    """Get current active email account"""
    return EMAIL_ACCOUNTS[CURRENT_EMAIL_INDEX]

def rotate_email():
    """Rotate to next email account"""
    global CURRENT_EMAIL_INDEX
    
    old_index = CURRENT_EMAIL_INDEX
    old_email = EMAIL_ACCOUNTS[old_index]["email"]
    
    # Cari email berikutnya yang masih kuota
    for i in range(1, len(EMAIL_ACCOUNTS) + 1):
        next_index = (CURRENT_EMAIL_INDEX + i) % len(EMAIL_ACCOUNTS)
        if EMAIL_ACCOUNTS[next_index]["sent_count"] < EMAIL_ACCOUNTS[next_index]["max_per_account"]:
            CURRENT_EMAIL_INDEX = next_index
            break
    else:
        # Jika semua email habis kuota, reset semua
        logger.warning("🔄 All email quotas exceeded, resetting counts")
        for account in EMAIL_ACCOUNTS:
            account["sent_count"] = 0
        CURRENT_EMAIL_INDEX = 0
    
    new_email = EMAIL_ACCOUNTS[CURRENT_EMAIL_INDEX]["email"]
    logger.info("🔄 Email rotated: %s → %s", old_email, new_email)
    save_email_stats()
    
    return new_email

def update_email_stats(success: bool = True):
    """Update email statistics after sending"""
    current_email = get_current_email()
    
    if success:
        current_email["sent_count"] += 1
        logger.info("📧 Email %s: %d/%d sent", 
                   current_email["email"], 
                   current_email["sent_count"], 
                   current_email["max_per_account"])
        
        # Cek jika perlu rotate
        if current_email["sent_count"] >= current_email["max_per_account"]:
            new_email = rotate_email()
            return new_email
    
    save_email_stats()
    return current_email["email"]

def get_email_status() -> str:
    """Get status of all email accounts"""
    status = []
    for i, account in enumerate(EMAIL_ACCOUNTS):
        current = "📍" if i == CURRENT_EMAIL_INDEX else "  "
        status.append(
            f"{current} {account['email']}: {account['sent_count']}/{account['max_per_account']}"
        )
    return "\n".join(status)

# ---------------- persistence helpers ----------------
def load_allowed() -> Set[int]:
    s = set()
    if os.path.exists(ALLOWED_FILE):
        try:
            with open(ALLOWED_FILE, "r") as f:
                for line in f:
                    t = line.strip()
                    if t.isdigit():
                        s.add(int(t))
        except Exception as e:
            logger.warning("Failed reading allowed file: %s", e)
    return s

def save_allowed():
    try:
        with open(ALLOWED_FILE, "w") as f:
            for uid in sorted(allowed_users):
                f.write(f"{uid}\n")
    except Exception as e:
        logger.warning("Failed saving allowed file: %s", e)

def load_stats():
    global stats
    if not os.path.exists(STATS_FILE):
        return
    try:
        with open(STATS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k in ("sent", "failed"):
                    try:
                        stats[k] = int(v)
                    except:
                        stats[k] = 0
                elif k == "users":
                    stats["users"] = set(map(int, v.split(","))) if v else set()
                elif k == "numbers":
                    stats["numbers"] = set(v.split(",")) if v else set()
                elif k == "user_counts":
                    d = {}
                    if v:
                        for item in v.split(","):
                            if ":" in item:
                                a, b = item.split(":", 1)
                                try:
                                    d[int(a)] = int(b)
                                except:
                                    pass
                    stats["user_counts"] = d
    except Exception as e:
        logger.warning("Failed loading stats: %s", e)

def save_stats():
    try:
        with open(STATS_FILE, "w") as f:
            f.write(f"sent={stats['sent']}\n")
            f.write(f"failed={stats['failed']}\n")
            f.write(f"users={','.join(map(str, stats['users']))}\n")
            f.write(f"numbers={','.join(stats['numbers'])}\n")
            f.write(f"user_counts={','.join(f'{k}:{v}' for k, v in stats['user_counts'].items())}\n")
    except Exception as e:
        logger.warning("Failed saving stats: %s", e)

def load_config():
    global BOT_MODE, SEND_COOLDOWN_SECONDS
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        mode = data.get("mode")
        if mode in ("chat", "group", "all"):
            BOT_MODE = mode
        cd = data.get("send_cooldown_seconds")
        if isinstance(cd, int) and cd >= 0:
            SEND_COOLDOWN_SECONDS = cd
        logger.info("Loaded config: mode=%s send_cooldown=%s", BOT_MODE, SEND_COOLDOWN_SECONDS)
    except Exception as e:
        logger.warning("Failed loading config.json: %s", e)

async def save_config():
    async with _config_lock:
        try:
            tmp = {"mode": BOT_MODE, "send_cooldown_seconds": SEND_COOLDOWN_SECONDS}
            with open(CONFIG_FILE, "w") as f:
                json.dump(tmp, f)
            logger.info("Config saved.")
        except Exception as e:
            logger.warning("Failed saving config.json: %s", e)

# preload
allowed_users = load_allowed()
load_stats()
load_config()
load_email_stats()

# ---------------- helpers ----------------
def neon_header() -> str:
    return f"{NEON_BORDER}\nFUCK YOUR MOMS\n{NEON_BORDER}"

def is_allowed(uid: int) -> bool:
    return uid in allowed_users or uid == OWNER_ID

def is_update_before_start(update: Update) -> bool:
    if BOT_START_TIME is None:
        return False
    msg = update.effective_message
    if msg and getattr(msg, "date", None):
        try:
            if msg.date.replace(tzinfo=msg.date.tzinfo) < BOT_START_TIME:
                return True
        except Exception:
            pass
    if update.callback_query and update.callback_query.message and getattr(update.callback_query.message, "date", None):
        try:
            if update.callback_query.message.date.replace(tzinfo=update.callback_query.message.date.tzinfo) < BOT_START_TIME:
                return True
        except Exception:
            pass
    return False

# ---------------- SMTP send dengan ROTATION ----------------
def build_email_message(number: str, requester_id: int, user_name: str) -> MIMEText:
    subject = "Solicitação de ajuda para verificar seu número do WhatsApp. Prezado suporte do WhatsApp."
    body = (
        f"Olá, Prezada Equipe de Suporte do WhatsApp\n\n Gostaria de relatar um problema com meu número do WhatsApp. Quando crio uma conta no WhatsApp, sempre que entro, recebo uma mensagem e uma notificação dizendo Login Indisponível no Momento.Espero que o suporte do WhatsApp possa me ajudar a recuperar o acesso ao meu número do WhatsApp {number}\n\n"
        "Não estou recebendo os problemas ou mensagens que mencionei anteriormente ao suporte do WhatsApp. Obrigado pela ajuda, suporte do WhatsApp.\n\n\n"
        f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    return msg

def send_email_blocking(number: str, requester_id: int, user_name: str) -> Tuple[bool, Optional[str], str]:
    """Send email dengan rotation system"""
    current_email = get_current_email()
    msg = build_email_message(number, requester_id, user_name)
    msg["From"] = current_email["email"]
    msg["To"] = TO_EMAIL
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as server:
            server.login(current_email["email"], current_email["app_password"])
            server.sendmail(current_email["email"], TO_EMAIL, msg.as_string())
        
        # Update stats dan rotate jika perlu
        new_email = update_email_stats(success=True)
        return True, None, current_email["email"]
        
    except Exception as e:
        # Jika gagal, coba rotate email
        logger.warning("❌ Email %s failed: %s, rotating...", current_email["email"], e)
        rotate_email()
        return False, str(e), current_email["email"]

# ---------------- decorators ----------------
def require_mode(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if is_update_before_start(update):
            try:
                if update.callback_query:
                    await update.callback_query.answer()
                    if update.callback_query.message:
                        await update.callback_query.message.reply_text("⚠️ Tombol ini diklik dari pesan lama (bot offline). Silakan ulangi.")
                elif update.effective_message:
                    await update.effective_message.reply_text("⚠️ Pesan ini dikirim saat bot offline. Silakan kirim ulang sekarang bot sudah online.")
            except Exception:
                pass
            return

        if update.callback_query:
            return await func(update, context)

        chat = update.effective_chat
        if not chat:
            return

        if BOT_MODE == "chat" and chat.type != "private":
            try:
                await update.effective_message.reply_text("❗ Bot saat ini hanya bisa digunakan lewat chat pribadi (DM).")
            except Exception:
                pass
            return
        if BOT_MODE == "group" and chat.type == "private":
            try:
                await update.effective_message.reply_text("❗ Bot saat ini hanya bisa digunakan di grup.")
            except Exception:
                pass
            return

        return await func(update, context)
    return wrapper

def require_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id if update.effective_user else None
        if uid != OWNER_ID:
            try:
                await update.effective_message.reply_text("🚫 Hanya kayzii yang bisa menggunakan perintah ini.")
            except Exception:
                pass
            return
        return await func(update, context)
    return wrapper

# ---------------- Menu Button Helpers ----------------
def create_main_menu_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🆔 Dapatkan ID Saya", callback_data="menu_myid")],
    ]
    
    if user_id and is_allowed(user_id):
        keyboard.append([InlineKeyboardButton("📤 Kirim Banding", callback_data="menu_send")])
    else:
        keyboard.append([InlineKeyboardButton("🔔 Minta Akses", callback_data="menu_request_access")])
    
    keyboard.extend([
        [InlineKeyboardButton("1⃣ bantuan dan info bot", callback_data="menu_help")],
    ])
    
    if user_id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("👑 Menu Owner", callback_data="menu_owner")])
    
    return InlineKeyboardMarkup(keyboard)

def create_owner_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Statistik", callback_data="owner_stats")],
        [InlineKeyboardButton("📋 List Permintaan", callback_data="owner_list_requests")],
        [InlineKeyboardButton("👥 List User Aktif", callback_data="owner_list_users")],
        [InlineKeyboardButton("⚙️ coldown", callback_data="owner_set_cooldown")],
        [InlineKeyboardButton("🔧 Ganti Mode", callback_data="owner_change_mode")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast")],
        [InlineKeyboardButton("⏰ Mode 24 Jam", callback_data="owner_24h_mode")],
        [InlineKeyboardButton("📧 Status Email aktif", callback_data="owner_email_status")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_24h_menu_keyboard() -> InlineKeyboardMarkup:
    status = get_24h_status()
    is_enabled = status["enabled"]
    
    if status["process_running"]:
        status_text = "🟢 BERJALAN"
    elif status["restart_script_running"]:
        status_text = "🟡 SEDANG MULAI"
    elif is_enabled:
        status_text = "🟡 AKTIF (STOPPED)"
    else:
        status_text = "🔴 NONAKTIF"
    
    keyboard = [
        [InlineKeyboardButton(f"🔄 Status: {status_text}", callback_data="owner_24h_status")],
    ]
    
    if not is_enabled:
        keyboard.append([InlineKeyboardButton("🚀 Aktifkan 24 Jam", callback_data="owner_24h_enable")])
    else:
        keyboard.append([InlineKeyboardButton("🛑 Nonaktifkan 24 Jam", callback_data="owner_24h_disable")])
    
    if is_enabled and not status["process_running"]:
        keyboard.append([InlineKeyboardButton("▶️ Jalankan Sekarang", callback_data="owner_24h_start")])
    
    if status["process_running"]:
        keyboard.append([InlineKeyboardButton("⏸️ Hentikan Sementara", callback_data="owner_24h_stop")])
    
    keyboard.append([InlineKeyboardButton("📋 Cara Pakai", callback_data="owner_24h_help")])
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")])
    
    return InlineKeyboardMarkup(keyboard)

def create_back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu_main")]])

# ---------------- FIXED Callback Handler ----------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ALL callbacks in one place"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    print(f"🔘 Button clicked: {data} by user {user_id}")
    
    try:
        # Menu utama
        if data == "menu_main":
            text = "🎯 *Menu Utama Bot*\n\nPilih opsi di bawah:"
            keyboard = create_main_menu_keyboard(user_id)
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "menu_myid":
            text = f"🆔 *ID Telegram Anda:*\n`{user_id}`\n\nGunakan ID ini untuk minta akses ke kayzii."
            keyboard = create_back_to_main_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "menu_send":
            if is_allowed(user_id):
                text = "📤 *Kirim Banding*\n\nGunakan perintah:\n`/banding +6281234567890`\n\nGanti dengan nomor WhatsApp Anda (format internasional)."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Kirim Sekarang", switch_inline_query_current_chat="/banding ")],
                    [InlineKeyboardButton("🔙 Kembali", callback_data="menu_main")]
                ])
            else:
                text = "❌ *Akses Ditolak oleh kayzii*\n\nAnda belum memiliki akses untuk mengirim banding. Silakan minta akses ke kayzii terlebih dahulu."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 Minta Akses ke owner kayzii", callback_data="menu_request_access")],
                    [InlineKeyboardButton("🔙 Kembali", callback_data="menu_main")]
                ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "menu_request_access":
            # Handle request access
            if is_allowed(user_id):
                await query.edit_message_text("✅ *Akses Diterima oleh kayzii*\n\nAnda sudah memiliki akses untuk menggunakan bot ini.", parse_mode="Markdown")
                return
            
            if user_id in pending_requests:
                await query.edit_message_text("⏳ *Permintaan Dikirim*\n\nPermintaan akses Anda sudah dikirim ke kayzii. Tunggu persetujuan.", parse_mode="Markdown")
                return
            
            now = time.time()
            last_req = request_cooldowns.get(user_id, 0)
            if now - last_req < REQUEST_COOLDOWN_SECONDS:
                remain = int(REQUEST_COOLDOWN_SECONDS - (now - last_req))
                await query.edit_message_text(f"⏳ Kamu baru meminta akses. Tunggu {remain}s.", parse_mode="Markdown")
                return
            
            requester_name = query.from_user.full_name or query.from_user.username or str(user_id)
            request_text = (
                f"🔔 *Permintaan Akses Baru*\n\n"
                f"👤 Nama: `{requester_name}`\n"
                f"🆔 ID: `{user_id}`\n"
                f"📅 Waktu: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                "Tekan tombol di bawah untuk memberikan akses:"
            )
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ terima akses bos", callback_data=f"approve:{user_id}")],
                [InlineKeyboardButton("❌ Tolak akses bos", callback_data=f"reject:{user_id}")],
            ])
            
            try:
                await context.bot.send_message(
                    chat_id=OWNER_ID, 
                    text=request_text, 
                    parse_mode="Markdown", 
                    reply_markup=kb
                )
                pending_requests.add(user_id)
                request_cooldowns[user_id] = now
                
                success_text = (
                    "✅ *Permintaan Terkirim!*\n\n"
                    "Permintaan akses telah dikirim ke owner. \n"
                    "Tunggu persetujuan oleh bos kayzii."
                )
                keyboard = create_back_to_main_keyboard()
                await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=keyboard)
                
                logger.info("📩 Access request sent to owner for uid=%s", user_id)
            except Exception as e:
                error_text = "❌ *Gagal Mengirim*\n\nGagal mengirim permintaan ke owner. Coba lagi nanti."
                keyboard = create_back_to_main_keyboard()
                await query.edit_message_text(error_text, parse_mode="Markdown", reply_markup=keyboard)
                logger.error("Failed to send request to owner: %s", e)
        
        elif data == "menu_help":
            # Help callback
            mode_label = {
                "chat": "Chat Pribadi",
                "group": "Grup (Owner/Allowed Only)",
                "all": "Chat & Grup"
            }.get(BOT_MODE, BOT_MODE)

            text = (
                "❓ *Bantuan & Informasi*\n\n"
                "🤖 *Tentang Bot:*\n"
                "Bot ini membantu mengirim banding ke support WhatsApp untuk masalah \"number cannot be registered\".\n\n"
                
                "🎯 *Cara Menggunakan:*\n"
                "1. Dapatkan ID Telegram Anda\n"
                "2. Minta akses ke owner\n"
                "3. Kirim banding dengan nomor WhatsApp\n\n"
                
                "⚡ *Fitur:*\n"
                "• Proses otomatis dan cepat\n"
                "• Notifikasi real-time\n"
                "• Keamanan terjamin\n"
                "• 📧 Rotasi Email Otomatis\n"
                "• ⏰ Mode 24 Jam (Auto-restart)\n\n"
                
                f"🔧 *Konfigurasi:*\n"
                f"• Mode: `{mode_label}`\n"
                f"• Cooldown: `{SEND_COOLDOWN_SECONDS}s`\n\n"
                
                "💬 *Butuh Bantuan?*\n"
                "Hubungi owner jika mengalami masalah."
            )
            
            keyboard = create_main_menu_keyboard(user_id)
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "menu_owner":
            if user_id == OWNER_ID:
                text = "👑 owner kayzii\n\nPilih opsi di bawah:"
                keyboard = create_owner_menu_keyboard()
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                text = "🚫 *Akses Ditolak oleh kayzii*\n\nHanya kayzii yang bisa mengakses menu ini."
                keyboard = create_back_to_main_keyboard()
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        # Menu Owner
        elif data == "owner_stats":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya kayzii yang bisa menggunakan menu ini.")
                return
            
            sent = stats["sent"]
            failed = stats["failed"]
            total_users = len(stats["users"])
            total_numbers = len(stats["numbers"])
            allowed_count = len(allowed_users)
            
            # Get 24h status
            status_24h = get_24h_status()
            is_24h = status_24h["enabled"]
            is_running = status_24h["process_running"]
            
            text = (
                f"📊 *Statistik Bot*\n\n"
                f"✅ Banding Terkirim: `{sent}`\n"
                f"❌ Gagal Dikirim: `{failed}`\n"
                f"👥 User Unik: `{total_users}`\n"
                f"📱 Nomor Unik: `{total_numbers}`\n"
                f"🔓 User Aktif: `{allowed_count}`\n"
                f"⏳ Pending Requests: `{len(pending_requests)}`\n"
                f"🔧 Mode: `{BOT_MODE}`\n"
                f"⏰ Cooldown: `{SEND_COOLDOWN_SECONDS}s`\n"
                f"🏃 Mode 24 Jam: `{'🟢 BERJALAN' if is_running else '🟡 AKTIF' if is_24h else '🔴 NONAKTIF'}`"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="owner_stats")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_list_requests":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            if not pending_requests:
                text = "✅ Tidak ada permintaan akses bos."
            else:
                text = "🔔 *Permintaan Akses pending bos:*\n\n" + "\n".join(f"• `{uid}`" for uid in sorted(pending_requests))
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="owner_list_requests")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_list_users":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya kayzii yang bisa menggunakan menu ini.")
                return
            
            if not allowed_users:
                text = "ℹ️ Belum ada user yang diizinkan menggunakan bot."
            else:
                text = "👥 *User yang Diizinkan:*\n\n" + "\n".join(f"• `{uid}`" for uid in sorted(allowed_users))
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="owner_list_users")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_set_cooldown":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            text = f"⚙️ *Set Cooldown*\n\nCooldown saat ini: `{SEND_COOLDOWN_SECONDS}s`\n\nGunakan perintah:\n`/setcooldown <detik>`\n\nContoh: `/setcooldown 300`"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Set Sekarang", switch_inline_query_current_chat="/setcooldown ")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_change_mode":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            text = f"🔧 *Ganti Mode Bot*\n\nMode saat ini: `{BOT_MODE}`\n\nPilihan mode:\n• `chat` - Hanya chat pribadi\n• `group` - Hanya grup\n• `all` - Semua jenis chat\n\nGunakan perintah:\n`/mode <chat|group|all>`"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Ganti Mode", switch_inline_query_current_chat="/mode ")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_broadcast":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            text = "📢 *Broadcast Message*\n\nGunakan perintah:\n`/bc <pesan Anda>`\n\nContoh: `/bc Hai semua, ada update baru!`"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Broadcast Sekarang", switch_inline_query_current_chat="/bc ")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        # 24 Jam Mode Buttons - FIXED
        elif data == "owner_24h_mode":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya kayzii yang bisa menggunakan menu ini.")
                return
            
            text = "⏰ *Mode 24 Jam*\n\nAtur bot untuk berjalan 24 jam secara otomatis meski Termux ditutup."
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_24h_status":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            status = get_24h_status()
            is_enabled = status["enabled"]
            is_running = status["process_running"]
            pid = status["pid"]
            
            if is_running:
                status_text = f"🟢 BERJALAN (PID: {pid})"
            elif status["restart_script_running"]:
                status_text = "🟡 SEDANG MULAI"
            elif is_enabled:
                status_text = "🟡 AKTIF (DISTOP)"
            else:
                status_text = "🔴 NONAKTIF"
            
            text = (
                f"⏰ *Status Mode 24 Jam*\n\n"
                f"• Status: {status_text}\n"
                f"• Script: {'✅ Ada' if status['script_exists'] else '❌ Tidak Ada'}\n"
                f"• PID File: {'✅ Ada' if status['pid_file_exists'] else '❌ Tidak Ada'}\n"
                f"• Bot Process: {'✅ Running' if is_running else '❌ Stopped'}\n"
                f"• Restart Script: {'✅ Running' if status['restart_script_running'] else '❌ Stopped'}\n\n"
                f"🔄 *Auto Features:*\n"
                f"• Auto-restart jika crash\n"
                f"• Tetap hidup walau Termux ditutup\n"
                f"• Monitoring real-time"
            )
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_24h_enable":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            if enable_24h():
                text = (
                    "✅ *Mode 24 Jam Diaktifkan!*\n\n"
                    "Bot akan auto-restart jika mati/crash.\n\n"
                    "📝 **Langkah selanjutnya:**\n"
                    "1. **Klik 'Jalankan Sekarang'** di bawah\n"
                    "2. **Atau** di Termux: `./restart_24h.sh`\n\n"
                    "💡 **Tips:**\n"
                    "• Bot akan tetap hidup meski Termux ditutup\n"
                    "• Auto-restart jika ada error\n"
                    "• Log: `tail -f bot_24h.log`"
                )
            else:
                text = "❌ Gagal mengaktifkan mode 24 jam."
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_24h_disable":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            if disable_24h():
                text = "✅ *Mode 24 Jam Dinonaktifkan!*\n\nBot tidak akan restart otomatis lagi."
            else:
                text = "❌ Gagal menonaktifkan mode 24 jam."
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_24h_start":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            if not is_24h_enabled():
                text = "❌ Mode 24 jam belum diaktifkan. Aktifkan terlebih dahulu."
                keyboard = create_24h_menu_keyboard()
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
                return
            
            # Start the 24h process
            success, message = start_24h_process()
            
            if success:
                text = (
                    f"🚀 *Bot 24 Jam Dimulai!*\n\n"
                    f"{message}\n\n"
                    "📊 **Status:**\n"
                    "• Bot akan berjalan di background\n"
                    "• Auto-restart jika crash\n"
                    "• Tetap hidup walau Termux ditutup\n\n"
                    "📝 **Monitoring:**\n"
                    "• Log: `tail -f bot_24h.log`\n"
                    "• Status: Refresh menu ini"
                )
            else:
                text = f"❌ *Gagal Memulai Bot 24 Jam:*\n\n{message}"
            
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_24h_stop":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            stop_24h_process()
            text = "⏸️ *Bot 24 Jam Dihentikan Sementara*\n\nBot berhenti tetapi mode 24 jam masih aktif. Klik 'Jalankan Sekarang' untuk memulai lagi."
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_24h_help":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            text = (
                "📋 *Cara Menggunakan Mode 24 Jam:*\n\n"
                "**1. AKTIFKAN MODE:**\n"
                "• Klik 'Aktifkan 24 Jam' di menu\n\n"
                "**2. JALANKAN BOT:**\n"
                "• **Opsi A:** Klik 'Jalankan Sekarang' di menu\n"
                "• **Opsi B:** Di Termux: `./restart_24h.sh`\n\n"
                "**3. TUTUP TERMUX:**\n"
                "• Bot tetap berjalan di background\n"
                "• Auto-restart jika crash\n\n"
                "**4. MONITORING:**\n"
                "• Cek log: `tail -f bot_24h.log`\n"
                "• Cek status di menu bot\n"
                "• Tombol akan update otomatis\n\n"
                "**5. KONTROL:**\n"
                "• ⏸️ Hentikan Sementara - Stop bot tapi mode tetap aktif\n"
                "• 🛑 Nonaktifkan - Matikan mode 24 jam\n"
                "• ▶️ Jalankan - Mulai bot lagi\n\n"
                "⚡ **Fitur:**\n"
                "• Auto-restart jika bot crash\n"
                "• Tetap hidup walau Termux ditutup\n"
                "• Tombol kontrol real-time"
            )
            keyboard = create_24h_menu_keyboard()
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        # Email Status Handler
        elif data == "owner_email_status":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            current_email = get_current_email()
            email_status = get_email_status()
            
            text = (
                "📧 *Status Email Accounts*\n\n"
                f"{email_status}\n\n"
                f"📍 *Email Aktif:* `{current_email['email']}`\n"
                f"📊 *Usage:* `{current_email['sent_count']}/{current_email['max_per_account']}`\n\n"
                "🔄 *Auto Rotation:* Setiap 30 kiriman\n"
                "⚡ *Fitur:* Ganti otomatis jika email gagal"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="owner_email_status")],
                [InlineKeyboardButton("🔄 Rotate Manual", callback_data="owner_email_rotate")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        elif data == "owner_email_rotate":
            if user_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya owner yang bisa menggunakan menu ini.")
                return
            
            old_email = get_current_email()["email"]
            new_email = rotate_email()
            
            text = (
                "🔄 *Email Dirotate Manual*\n\n"
                f"📧 *Dari:* `{old_email}`\n"
                f"📧 *Ke:* `{new_email}`\n\n"
                "✅ Rotasi berhasil!"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📧 Status Email", callback_data="owner_email_status")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]
            ])
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
        # Approval system
        elif data.startswith("approve:") or data.startswith("reject:"):
            # Handle owner approval/rejection
            owner_id = query.from_user.id
            if owner_id != OWNER_ID:
                await query.edit_message_text("🚫 Hanya kayzii yang bisa melakukan aksi ini.")
                return
            
            if ":" not in data:
                await query.edit_message_text("⚠️ Data tidak valid.")
                return
            
            action, user_id_str = data.split(":", 1)
            
            try:
                target_uid = int(user_id_str)
            except ValueError:
                await query.edit_message_text("⚠️ ID user tidak valid.")
                return
            
            try:
                user_chat = await context.bot.get_chat(target_uid)
                user_name = user_chat.full_name or user_chat.username or str(target_uid)
            except Exception as e:
                user_name = "Unknown"
                logger.warning("Could not get user info for %s: %s", target_uid, e)
            
            if action == "approve":
                allowed_users.add(target_uid)
                save_allowed()
                pending_requests.discard(target_uid)
                
                approved_text = (
                    f"✅ *Akses Disetujui oleh kayzii!*\n\n"
                    f"👤 User: `{user_name}`\n"
                    f"🆔 ID: `{target_uid}`\n"
                    f"⏰ Waktu: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                await query.edit_message_text(approved_text, parse_mode="Markdown")
                
                user_notification = (
                    "🎉 *SELAMAT! Akses Anda Disetujui!*\n\n"
                    "Sekarang Anda dapat menggunakan fitur kirim banding WhatsApp.\n\n"
                    "✨ *Yang bisa dilakukan:*\n"
                    "• 📤 Kirim banding ke support WhatsApp\n"
                    "• ⚡ Proses otomatis dan cepat\n"
                    "• 🔒 Keamanan terjamin\n\n"
                    "Gunakan menu di bawah untuk mulai:"
                )
                
                try:
                    keyboard = create_main_menu_keyboard(target_uid)
                    await context.bot.send_message(
                        chat_id=target_uid,
                        text=user_notification,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    logger.info("✅ Owner APPROVED access for %s (uid=%s)", user_name, target_uid)
                except Exception as e:
                    logger.warning("❌ Could not DM approved user %s: %s", target_uid, e)
                    
            elif action == "reject":
                pending_requests.discard(target_uid)
                
                rejected_text = (
                    f"❌ *Akses Ditolak oleh kayzii*\n\n"
                    f"👤 User: `{user_name}`\n"
                    f"🆔 ID: `{target_uid}`\n"
                    f"⏰ Waktu: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                await query.edit_message_text(rejected_text, parse_mode="Markdown")
                
                try:
                    await context.bot.send_message(
                        chat_id=target_uid,
                        text="❌ Maaf, permintaan akses Anda ditolak oleh owner.\n\nSilakan hubungi owner untuk informasi lebih lanjut.",
                        parse_mode="Markdown"
                    )
                    logger.info("❌ Owner REJECTED access for %s (uid=%s)", user_name, target_uid)
                except Exception as e:
                    logger.warning("⚠️ Could not DM rejected user %s: %s", target_uid, e)
        
        else:
            # Fallback untuk button yang tidak dikenali
            await query.edit_message_text("⚠️ Tombol tidak dikenali. Silakan gunakan menu yang tersedia.")
            print(f"❌ Unknown button: {data}")
    
    except Exception as e:
        print(f"💥 Error in callback handler: {e}")
        await query.edit_message_text("❌ Terjadi error. Silakan coba lagi.")

# ---------------- Command Handlers ----------------
@require_mode
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        registered_chats.add(chat_id)
    except Exception:
        pass

    uid = update.effective_user.id if update.effective_user else None
    
    mode_label = {
        "chat": "Chat Pribadi",
        "group": "Grup (Owner/Allowed Only)",
        "all": "Chat & Grup"
    }.get(BOT_MODE, BOT_MODE)

    text = (
        "👋 *Selamat Datang di script bot banding kayzii new eraa*\n\n"
        "✨ *Fitur Utama script kayzii new eraa:*\n"
        "• 🆔 Dapatkan ID Telegram Anda\n"
        "• 📤 Kirim banding ke support WhatsApp\n"
        "• 🔔 Minta akses ke owner\n"
        "• ⚡ Proses cepat dan aman\n"
        "• ⏰ Mode 24 Jam (Owner Only)\n"
        "• 📧 Rotasi Email Otomatis\n\n"
        f"🔧 *Mode:* `{mode_label}`\n"
        f"⏰ *Cooldown:* `{SEND_COOLDOWN_SECONDS}s`\n\n"
        "Pilih menu di bawah untuk memulai:"
    )
    
    keyboard = create_main_menu_keyboard(uid)
    
    try:
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        if update.message:
            await update.message.reply_text(text.replace("*", ""), reply_markup=keyboard)
        else:
            await update.callback_query.message.reply_text(text.replace("*", ""), reply_markup=keyboard)

@require_mode
async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_name = update.effective_user.full_name or update.effective_user.username or str(uid)

    if not is_allowed(uid):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Minta Akses", callback_data="menu_request_access")],
            [InlineKeyboardButton("📋 Menu Utama", callback_data="menu_main")]
        ])
        return await update.message.reply_text(
            "🚫 Kamu belum diberi akses. Minta akses ke owner terlebih dahulu.", 
            reply_markup=keyboard
        )

    if not context.args:
        return await update.message.reply_text(
            "✍️ Gunakan: `/banding +62xxxxxxxxx`\n\nContoh: `/banding +6281234567890`", 
            parse_mode="Markdown"
        )

    number = context.args[0].strip()

    if not number.startswith('+'):
        return await update.message.reply_text(
            "❌ Format nomor tidak valid. Gunakan format internasional dengan kode negara.\nContoh: `+6281234567890`",
            parse_mode="Markdown"
        )

    now = time.time()
    last_send = user_last_send.get(uid, 0)
    if now - last_send < SEND_COOLDOWN_SECONDS:
        remain = int(SEND_COOLDOWN_SECONDS - (now - last_send))
        return await update.message.reply_text(
            f"⏳ banding telah dikirim oleh kayzii tolong ditunggu `{remain}` detik sebelum mengirim banding lagi.",
            parse_mode="Markdown"
        )

    current_email = get_current_email()
    logger.info("🚀 Starting appeal process for %s (uid=%s) - Number: %s - Email: %s", 
                user_name, uid, number, current_email["email"])
    
    sending_msg = await update.message.reply_text("🚀 *Mengirim Banding* • [          ] 0%", parse_mode="Markdown")
    
    try:
        for i in range(1, PROGRESS_STEPS + 1):
            pct = int((i / PROGRESS_STEPS) * 100)
            bar = "█" * i + " " * (PROGRESS_STEPS - i)
            await asyncio.sleep(ANIM_DELAY)
            try:
                await sending_msg.edit_text(f"🚀 *Mengirim Banding* • [{bar}] {pct}%", parse_mode="Markdown")
            except Exception:
                pass

        logger.info("📧 Sending email appeal for %s (uid=%s) using %s", user_name, uid, current_email["email"])
        ok, err, used_email = await asyncio.get_running_loop().run_in_executor(
            None, send_email_blocking, number, uid, user_name
        )
        
        if ok:
            user_last_send[uid] = now
            stats["sent"] += 1
            stats["users"].add(uid)
            stats["numbers"].add(number)
            stats["user_counts"][uid] = stats["user_counts"].get(uid, 0) + 1
            save_stats()
            
            # Cek jika email dirotate
            new_email = get_current_email()["email"]
            rotation_note = ""
            if new_email != used_email:
                rotation_note = f"\n🔄 *Email rotated to:* `{new_email}`"
            
            success_text = (
                f"✅ *Banding Terkirim Sukses bos kayzii*\n\n"
                f"📱 Nomor: `{number}`\n"
                f"👤 Pengirim: `{user_name}`\n"
                f"📧 Email Used: `{used_email}`\n"
                f"📊 Usage: `{get_current_email()['sent_count']}/{get_current_email()['max_per_account']}`\n"
                f"⏰ Cooldown: `{SEND_COOLDOWN_SECONDS}s`"
                f"{rotation_note}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Menu Utama", callback_data="menu_main")],
                [InlineKeyboardButton("📤 Kirim Lagi", callback_data="menu_send")]
            ])
            
            await sending_msg.edit_text(success_text, parse_mode="Markdown", reply_markup=keyboard)
            logger.info("✅ Appeal SUCCESS for %s (uid=%s) - Email: %s", user_name, uid, used_email)
            
            if NOTIFY_OWNER_ON_SEND:
                try:
                    notify_text = (
                        f"📣 *Banding telah terkirim sukses bos kayzii*\n\n"
                        f"👤 User: `{user_name}`\n"
                        f"🆔 ID: `{uid}`\n"
                        f"📱 Nomor: `{number}`\n"
                        f"📧 Email: `{used_email}`\n"
                        f"📊 Usage: `{get_current_email()['sent_count']}/{get_current_email()['max_per_account']}`\n"
                        f"⏰ Waktu: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                    await context.bot.send_message(chat_id=OWNER_ID, text=notify_text, parse_mode="Markdown")
                except Exception as e:
                    logger.warning("❌ Could not notify owner: %s", e)
                    
        else:
            stats["failed"] += 1
            save_stats()
            
            error_text = (
                f"❌ *Gagal Mengirim Banding bos kayzii*\n\n"
                f"📱 Nomor: `{number}`\n"
                f"📧 Email: `{used_email}`\n"
                f"⚠️ Error: `{err}`\n\n"
                f"🔄 Mencoba email lain... Silakan coba lagi."
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Coba Lagi", callback_data="menu_send")],
                [InlineKeyboardButton("📋 Menu Utama", callback_data="menu_main")]
            ])
            
            await sending_msg.edit_text(error_text, parse_mode="Markdown", reply_markup=keyboard)
            logger.error("❌ Appeal FAILED for %s (uid=%s) - Error: %s", user_name, uid, err)
            
    except Exception as e:
        logger.exception("💥 Unexpected error in sending flow for %s: %s", user_name, e)
        try:
            error_msg = (
                f"❌ *Terjadi Kesalahan bos*\n\n"
                f"System error: `{str(e)}`\n\n"
                f"Silakan coba lagi atau hubungi owner."
            )
            await sending_msg.edit_text(error_msg, parse_mode="Markdown")
        except Exception:
            pass

@require_mode
async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"🪪 *ID Telegram Anda:*\n`{uid}`", parse_mode="Markdown")

@require_mode
async def list_requests_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Hanya kayzii yang bisa melihat permintaan.")
    if not pending_requests:
        return await update.message.reply_text("✅ Tidak ada permintaan saat ini bos kayzii.")
    text = "🔔 *Pending Requests:*\n\n" + "\n".join(f"- `{uid}`" for uid in sorted(pending_requests))
    await update.message.reply_markdown(text)

@require_mode
async def revoke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Hanya kayzii yang bisa mencabut akses.")
    if not context.args:
        return await update.message.reply_text("✍️ Gunakan: /revoke <user_id>")
    try:
        target = int(context.args[0])
    except:
        return await update.message.reply_text("⚠️ ID tidak valid.")
    if target in allowed_users:
        allowed_users.remove(target)
        save_allowed()
        await update.message.reply_text(f"✅ Akses ID `{target}` dicabut.", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target, text="⚠️ Akses kamu telah dicabut oleh kayzii.")
        except Exception:
            pass
        logger.info("🔒 Owner revoked access for uid=%s", target)
    else:
        await update.message.reply_text("ℹ️ ID tidak ada di daftar akses.")

@require_mode
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Hanya kayzii yang bisa melihat statistik.")
    sent = stats["sent"]
    failed = stats["failed"]
    total_users = len(stats["users"])
    total_numbers = len(stats["numbers"])
    text = (
        f"📊 Statistik\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"👥 Users unique: {total_users}\n"
        f"📱 Numbers unique: {total_numbers}\n"
    )
    await update.message.reply_text(text)

@require_mode
async def bc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Hanya owner yang bisa broadcast.")
    if not context.args:
        return await update.message.reply_text("✍️ Gunakan: /bc <pesan>")
    message = " ".join(context.args)
    users = sorted(allowed_users)
    if not users:
        return await update.message.reply_text("⚠️ Belum ada user terdaftar.")
    
    logger.info("📢 Owner starting broadcast to %s users", len(users))
    await update.message.reply_text(f"📢 Mengirim ke {len(users)} user (mulai)...")
    
    success = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 *Broadcast Owner*\n\n{message}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(BC_DELAY_SECONDS)
        except Exception as e:
            logger.warning("❌ Failed BC to %s: %s", uid, e)
    
    logger.info("✅ Broadcast completed: %s/%s success", success, len(users))
    await update.message.reply_text(f"✅ Broadcast selesai: {success}/{len(users)} sukses.")

@require_mode
@require_owner
async def setcooldown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global SEND_COOLDOWN_SECONDS
    if not context.args:
        return await update.message.reply_text(f"Gunakan: /coldown <detik>\nSaat ini: {SEND_COOLDOWN_SECONDS}s")
    try:
        new_cd = int(context.args[0])
        if new_cd < 0:
            raise ValueError("neg")
    except Exception:
        return await update.message.reply_text("⚠️ Masukkan angka detik yang valid (>=0).")
    
    old_cd = SEND_COOLDOWN_SECONDS
    SEND_COOLDOWN_SECONDS = new_cd
    await save_config()
    
    logger.info("⚙️ Owner changed cooldown from %ss to %ss", old_cd, new_cd)
    await update.message.reply_text(f"✅ Cooldown /send diubah dari `{old_cd}s` menjadi `{SEND_COOLDOWN_SECONDS}s`.", parse_mode="Markdown")

@require_mode
@require_owner
async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_MODE
    if not context.args:
        return await update.message.reply_text(f"Gunakan: /mode <chat|group|all>\nMode saat ini: {BOT_MODE}")
    m = context.args[0].lower()
    if m not in ("chat", "group", "all"):
        return await update.message.reply_text("⚠️ Pilih mode: chat / group / all")
    
    old_mode = BOT_MODE
    BOT_MODE = m
    await save_config()
    
    logger.info("🔧 Owner changed mode from %s to %s", old_mode, BOT_MODE)
    await update.message.reply_text(f"✅ Mode bot diubah dari `{old_mode}` menjadi `{BOT_MODE}`.", parse_mode="Markdown")

@require_mode
@require_owner
async def run24h_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        is_enabled = is_24h_enabled()
        status = get_24h_status()
        is_running = status["process_running"]
        
        if is_running:
            status_text = f"🟢 BERJALAN (PID: {status['pid']})"
        elif status["restart_script_running"]:
            status_text = "🟡 SEDANG MULAI"
        elif is_enabled:
            status_text = "🟡 AKTIF (DISTOP)"
        else:
            status_text = "🔴 NONAKTIF"
            
        text = (
            f"⏰ *Mode 24 Jam:* {status_text}\n\n"
            "**Perintah:**\n"
            "• `/run24h on` - Aktifkan mode\n"
            "• `/run24h off` - Nonaktifkan mode\n"
            "• `/run24h status` - Cek status detail\n"
            "• `/run24h start` - Jalankan sekarang\n"
            "• `/run24h stop` - Hentikan sementara\n\n"
            "**Cara pakai:**\n"
            "1. Aktifkan mode dengan `/run24h on`\n"
            "2. Jalankan dengan `/run24h start`\n"
            "3. Tutup Termux - bot tetap jalan!"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
        return
    
    action = context.args[0].lower()
    
    if action in ["on", "enable", "aktifkan"]:
        if enable_24h():
            text = (
                "✅ *Mode 24 Jam Diaktifkan!*\n\n"
                "**Langkah selanjutnya:**\n"
                "1. **Jalankan:** `/run24h start`\n"
                "2. **Atau** di Termux: `./restart_24h.sh`\n"
                "3. **Tutup Termux** - bot tetap hidup!\n\n"
                "📝 Log: `tail -f bot_24h.log`\n"
                "🛑 Stop: `/run24h off`"
            )
        else:
            text = "❌ Gagal mengaktifkan mode 24 jam."
    
    elif action in ["off", "disable", "nonaktifkan"]:
        if disable_24h():
            text = "✅ *Mode 24 Jam Dinonaktifkan!*\n\nBot tidak akan restart otomatis."
        else:
            text = "❌ Gagal menonaktifkan mode 24 jam."
    
    elif action in ["status", "info"]:
        status = get_24h_status()
        is_enabled = status["enabled"]
        is_running = status["process_running"]
        pid = status["pid"]
        
        if is_running:
            status_text = f"🟢 BERJALAN (PID: {pid})"
        elif status["restart_script_running"]:
            status_text = "🟡 SEDANG MULAI"
        elif is_enabled:
            status_text = "🟡 AKTIF (DISTOP)"
        else:
            status_text = "🔴 NONAKTIF"
            
        text = (
            f"⏰ *Status Detail Mode 24 Jam*\n\n"
            f"• Status: {status_text}\n"
            f"• Script: {'✅ Ada' if status['script_exists'] else '❌ Tidak Ada'}\n"
            f"• PID File: {'✅ Ada' if status['pid_file_exists'] else '❌ Tidak Ada'}\n"
            f"• Bot Process: {'✅ Running' if is_running else '❌ Stopped'}\n"
            f"• Restart Script: {'✅ Running' if status['restart_script_running'] else '❌ Stopped'}"
        )
    
    elif action in ["start", "run", "jalankan"]:
        if not is_24h_enabled():
            text = "❌ Mode 24 jam belum diaktifkan. Gunakan `/run24h on` terlebih dahulu."
        else:
            success, message = start_24h_process()
            if success:
                text = (
                    f"🚀 *Bot 24 Jam Dimulai!*\n\n"
                    f"{message}\n\n"
                    "📊 **Status:**\n"
                    "• Bot akan berjalan di background\n"
                    "• Auto-restart jika crash\n"
                    "• Tetap hidup walau Termux ditutup\n\n"
                    "📝 **Monitoring:**\n"
                    "• Log: `tail -f bot_24h.log`\n"
                    "• Status: `/run24h status`"
                )
            else:
                text = f"❌ *Gagal Memulai Bot 24 Jam:*\n\n{message}"
    
    elif action in ["stop", "pause", "hentikan"]:
        stop_24h_process()
        text = "⏸️ *Bot 24 Jam Dihentikan Sementara*\n\nBot berhenti tetapi mode 24 jam masih aktif. Gunakan `/run24h start` untuk memulai lagi."
    
    else:
        text = "❌ Perintah tidak valid. Gunakan: `/run24h on/off/status/start/stop`"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------------- Main Function ----------------
def main():
    global BOT_START_TIME
    
    BOT_START_TIME = datetime.now(timezone.utc)
    
    print("🚀 Starting Bot with EMAIL ROTATION & 24H FIX...")
    print("📧 Email Rotation: 3 accounts, 10 sends each")
    print("🔧 Mode:", BOT_MODE)
    print("⏰ Cooldown:", SEND_COOLDOWN_SECONDS, "seconds")
    
    # Print 24h status
    status_24h = get_24h_status()
    if status_24h["enabled"]:
        if status_24h["process_running"]:
            print(f"⏰ 24h Mode: 🟢 RUNNING (PID: {status_24h['pid']})")
        elif status_24h["restart_script_running"]:
            print("⏰ 24h Mode: 🟡 STARTING...")
        else:
            print("⏰ 24h Mode: 🟡 ENABLED (stopped)")
    else:
        print("⏰ 24h Mode: 🔴 DISABLED")
    
    # Print email status
    current_email = get_current_email()
    print(f"📧 Current Email: {current_email['email']} ({current_email['sent_count']}/{current_email['max_per_account']})")
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        # Register command handlers
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("x", start_cmd))
        app.add_handler(CommandHandler("help_kayzii", start_cmd))
        app.add_handler(CommandHandler("myid", myid_cmd))
        app.add_handler(CommandHandler("banding", send_cmd))
        app.add_handler(CommandHandler("listakses", list_requests_cmd))
        app.add_handler(CommandHandler("removeakses", revoke_cmd))
        app.add_handler(CommandHandler("statistik", stats_cmd))
        app.add_handler(CommandHandler("bc", bc_cmd))
        app.add_handler(CommandHandler("coldown", setcooldown_cmd))
        app.add_handler(CommandHandler("mode", mode_cmd))
        app.add_handler(CommandHandler("run24h", run24h_cmd))

        # Callback handler
        app.add_handler(CallbackQueryHandler(callback_handler))

        # Message handler
        app.add_handler(MessageHandler(filters.Regex(r"(?i)^\s*request\s*$"), start_cmd))

        print("✅ Bot started successfully!")
        print("💡 Press Ctrl+C to stop the bot")
        
        app.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"💥 Bot error: {e}")

if __name__ == "__main__":
    main()
