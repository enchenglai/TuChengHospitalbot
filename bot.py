import os
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 偽裝成一般 Chrome 瀏覽器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://register.cgmh.org.tw/',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
}

BASE_URL = "https://register.cgmh.org.tw/Progress/V?醫院=7"

def get_latest_menu():
    """自動抓取網頁上目前的科別清單 (加入 Header 偽裝)"""
    try:
        # 增加 timeout 防止卡死，加入 headers 避免被擋
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8' # 強制編碼避免亂碼
        soup = BeautifulSoup(response.text, 'html.parser')
        
        dept_select = soup.find('select', {'name': 'dept'})
        depts = {}
        if dept_select:
            for option in dept_select.find_all('option'):
                val = option.get('value')
                name = option.text.strip()
                if val and val != "00":
                    depts[val] = name
        return depts
    except Exception as e:
        print(f"抓取選單錯誤: {e}")
        # 若抓取失敗，回傳一組預設最常用的科別
        return {"04": "內科", "20": "牙科", "05": "外科", "06": "兒科"}

@bot.message_handler(commands=['start', 'check'])
def show_depts(message):
    bot.send_chat_action(message.chat.id, 'typing')
    current_depts = get_latest_menu()
    
    markup = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(name, callback_data=f"dept_{code}") for code, name in current_depts.items()]
    
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
        
    bot.send_message(message.chat.id, "🏥 請選擇要查詢的科別：", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dept_'))
def show_times(call):
    dept_code = call.data.split('_')[1]
    markup = InlineKeyboardMarkup()
    times = {"1": "☀️ 上午診", "2": "🌤 下午診", "3": "🌙 夜間診"}
    for code, name in times.items():
        markup.add(InlineKeyboardButton(name, callback_data=f"query_{dept_code}_{code}"))
    
    bot.edit_message_text("請選擇看診時段：", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('query_'))
def get_hospital_progress(call):
    _, dept, time_val = call.data.split('_')
    url = f"https://register.cgmh.org.tw/Progress/V?dept={dept}&time={time_val}"
    
    try:
        bot.answer_callback_query(call.id, "連線醫院伺服器中...")
        # 同樣加入偽裝與 Timeout
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.find_all('tr')
        found_any = False
        bot.delete_message(call.message.chat.id, call.message.message_id)

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                doctor = cols[1].text.strip()
                if "醫師" in doctor or not doctor: continue

                found_any = True
                msg = (
                    "=================================\n"
                    f"掛號科別 : {cols[0].text.strip()}\n"
                    f"醫師 : {doctor}\n"
                    f"目前看診號碼 : {cols[3].text.strip()}\n"
                    f"下一個看診號碼 : {cols[4].text.strip()}\n"
                    "================================="
                )
                bot.send_message(call.message.chat.id, msg)

        if not found_any:
            bot.send_message(call.message.chat.id, "📭 目前該時段沒有看診資料，請確認開診時間。")

    except Exception as e:
        print(f"連線錯誤: {e}")
        bot.send_message(call.message.chat.id, "❌ 連線被醫院伺服器拒絕，請稍後再試一次。\n(這可能是因為查詢過於頻繁)")

bot.polling(none_stop=True)
