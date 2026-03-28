import os
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 從 Render 的環境變數讀取 Token
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 土城醫院看診進度總入口
BASE_URL = "https://register.cgmh.org.tw/Progress/V?醫院=7"

def get_latest_menu():
    """自動抓取網頁上目前的科別清單"""
    try:
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找科別下拉選單 (通常是 <select name="dept">)
        dept_select = soup.find('select', {'name': 'dept'})
        depts = {}
        if dept_select:
            for option in dept_select.find_all('option'):
                val = option.get('value')
                name = option.text.strip()
                if val and val != "00": # 排除預設值
                    depts[val] = name
        return depts
    except:
        return {"04": "內科", "20": "牙科"} # 失敗時的備案

# 1. 收到 /check 時，動態抓取目前的科別
@bot.message_handler(commands=['start', 'check'])
def show_depts(message):
    bot.send_chat_action(message.chat.id, 'typing')
    current_depts = get_latest_menu()
    
    markup = InlineKeyboardMarkup()
    # 每列顯示兩個按鈕，比較美觀
    buttons = []
    for code, name in current_depts.items():
        buttons.append(InlineKeyboardButton(name, callback_data=f"dept_{code}"))
    
    # 將按鈕分組，每行 2 個
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
        
    bot.send_message(message.chat.id, "🔍 偵測到最新診間資訊，請選擇科別：", reply_markup=markup)

# 2. 選擇科別後，選擇時段 (時段通常固定為 1:上午, 2:下午, 3:夜間)
@bot.callback_query_handler(func=lambda call: call.data.startswith('dept_'))
def show_times(call):
    dept_code = call.data.split('_')[1]
    markup = InlineKeyboardMarkup()
    times = {"1": "☀️ 上午診", "2": "🌤 下午診", "3": "🌙 夜間診"}
    
    for code, name in times.items():
        markup.add(InlineKeyboardButton(name, callback_data=f"query_{dept_code}_{code}"))
    
    bot.edit_message_text("請選擇看診時段：", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

# 3. 抓取最終進度並格式化輸出
@bot.callback_query_handler(func=lambda call: call.data.startswith('query_'))
def get_hospital_progress(call):
    _, dept, time = call.data.split('_')
    url = f"https://register.cgmh.org.tw/Progress/V?dept={dept}&time={time}"
    
    try:
        bot.answer_callback_query(call.id, "正在查詢中...")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找進度表格
        rows = soup.find_all('tr')
        found_any = False
        
        # 刪除選單訊息
        bot.delete_message(call.message.chat.id, call.message.message_id)

        for row in rows:
            cols = row.find_all('td')
            # 根據長庚網頁欄位結構解析
            if len(cols) >=
