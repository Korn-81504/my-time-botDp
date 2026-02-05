import telebot
from telebot import types
from datetime import datetime, timedelta, timezone
from flask import Flask
from threading import Thread


# --- ข้อมูลสำคัญ ---
API_TOKEN = '8394178750:AAHbrlqPOgo2N7wYc_Mv5k3ETc6bupACX7A' 
GROUP_CHAT_ID =  3620177186
TARGET_THREAD_ID = 2

# แก้ปัญหา Error 403 โดยใช้ตัวแปรเก็บข้อมูลแทน Replit DB
temp_db = {}

STAFF_DAY = ["JIKORN✨", "AUDREY", "ANNY", "NANNY", "THIP", "NUMPUENG", "EMMI", "WAN WAN", "TOU", "NAY", "KHAK", "FERN", "PAN", "ALI", "NUS", "BOW", "DA", "HENG", "NIGH2", "VI"]
STAFF_NIGHT = ["NIGH", "NAMWAN", "ANWA", "TAE(REC)", "TAR(LA)", "NOUNU", "ANNIE", "CAO-KUAI", "MAY", "SENMI-LA", "BEAMF", "OIL-REC", "BELLE", "PREM", "JANE", "BEAMREC", "TEA 2"]

def get_thai_now():
    return datetime.now(timezone(timedelta(hours=7)))

app = Flask('')
@app.route('/')
def home(): return "บอทออนไลน์ปกติ"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

bot = telebot.TeleBot(API_TOKEN)

# แก้ปัญหา AttributeError โดยใช้การตั้งค่าเมนูแบบมาตรฐาน
def set_bot_menu():
    try:
        cmd = [types.BotCommand("start", "เริ่มบันทึกเวลา")]
        bot.set_my_commands(cmd) 
        print("✅ ตั้งค่าเมนูพื้นฐานสำเร็จ!")
    except Exception as e:
        print(f"⚠️ ตั้งเมนูไม่สำเร็จแต่บอทยังรันต่อได้: {e}")

def shift_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("☀️ กะเช้า (DAY)", callback_data="shift_DAY"),
               types.InlineKeyboardButton("🌙 กะดึก (NIGHT)", callback_data="shift_NIGHT"))
    markup.add(types.InlineKeyboardButton("❌ ยกเลิกและปิดเมนู", callback_data="delete_msg"))
    return markup

def name_markup(shift_code):
    markup = types.InlineKeyboardMarkup(row_width=3)
    staff_list = STAFF_DAY if shift_code == "DAY" else STAFF_NIGHT
    btns = [types.InlineKeyboardButton(name, callback_data=f"select_{shift_code}_{name}") for name in staff_list]
    markup.add(*btns)
    markup.add(types.InlineKeyboardButton("⬅️ ย้อนกลับ", callback_data="back_to_shift"),
               types.InlineKeyboardButton("❌ ยกเลิก", callback_data="delete_msg"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id == GROUP_CHAT_ID:
        # ดึง thread_id แบบปลอดภัยเพื่อรองรับ Library ทุกเวอร์ชัน
        t_id = getattr(message, 'message_thread_id', None)
        bot.send_message(message.chat.id, "🕒 **กรุณาเลือกกะการทำงาน:**", 
                         reply_markup=shift_markup(), 
                         message_thread_id=t_id, 
                         parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "delete_msg")
def delete_msg(call):
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

@bot.callback_query_handler(func=lambda c: c.data == "back_to_shift")
def back_to_shift(call):
    bot.edit_message_text("🕒 **กรุณาเลือกกะการทำงาน:**", call.message.chat.id, call.message.message_id, reply_markup=shift_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith('shift_'))
def handle_shift(call):
    shift_code = call.data.split('_')[1]
    bot.edit_message_text("👤 **กรุณาเลือกชื่อของคุณ:**", call.message.chat.id, call.message.message_id, reply_markup=name_markup(shift_code), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith('select_'))
def select_name(call):
    data = call.data.split('_')
    shift, name = data[1], data[2]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🍚 ซื้อของ", callback_data=f"out_{shift}_{name}_ซื้อของ"),
               types.InlineKeyboardButton("🚬 ดูดบุหรี่", callback_data=f"out_{shift}_{name}_ดูดบุหรี่"),
               types.InlineKeyboardButton("🚽เข้าห้องน้ำ", callback_data=f"out_{shift}_{name}_เข้าห้องน้ำ"))
    markup.add(types.InlineKeyboardButton("⬅️ ย้อนกลับ", callback_data=f"shift_{shift}"),
               types.InlineKeyboardButton("❌ ยกเลิก", callback_data="delete_msg"))
    bot.edit_message_text(f"👤 คุณ **{name}**\nไปทำอะไรดีครับ?", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith('out_'))
def handle_out(call):
    data = call.data.split('_')
    shift, name, activity = data[1], data[2], data[3]
    now = get_thai_now()
    msg_id = str(call.message.message_id)

    # บันทึกข้อมูลเข้าตัวแปร temp_db
    temp_db[msg_id] = f"{now.isoformat()}|{activity}|{name}|{shift}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"✨ {name} กลับมาแล้ว", callback_data=f"in_{msg_id}"))

    shift_label = "กะเช้า" if shift == "DAY" else "กะดึก"
    bot.edit_message_text(f"📍 **แจ้งเตือน ({shift_label})**\n👤 **{name}**\n🏃‍♂️ ไป: **{activity}**\n🕒 เวลาออก: {now.strftime('%H:%M:%S')}", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith('in_'))
def handle_in(call):
    msg_id = call.data.split('_')[1]
    now = get_thai_now()
    if msg_id in temp_db:
        raw_data = temp_db[msg_id].split('|')
        start_time = datetime.fromisoformat(raw_data[0]).replace(tzinfo=timezone(timedelta(hours=7)))
        activity, name, shift = raw_data[1], raw_data[2], raw_data[3]
        duration = now - start_time
        total_sec = int(duration.total_seconds())
        h, m, s = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60

        shift_label = "กะเช้า" if shift == "DAY" else "กะดึก"
        result_text = (f"📍 **สรุปเวลา ({shift_label})**\n👤 **{name}**\n🏃‍♂️ ไป: **{activity}**\n"
                       f"🕒 เวลาออก: {start_time.strftime('%H:%M:%S')}\n"
                       f"✨ กลับมาตอน: {now.strftime('%H:%M:%S')}\n"
                       f"⌛️ เวลารวม: **{h}:{m:02d}:{s:02d}**")

        del temp_db[msg_id]
        bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "❌ ไม่พบข้อมูล (อาจเพราะมีการรีสตาร์ทบอท)")

if __name__ == "__main__":
    keep_alive()
    set_bot_menu()
    print("🚀 บอทเริ่มทำงานแล้ว (โหมดแก้ไข Error)...")
    bot.infinity_polling()
