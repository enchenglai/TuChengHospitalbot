import os
import requests
from bs4 import BeautifulSoup
import telebot

# 從 Render 的環境變數讀取 Token
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'check'])
def send_progress(message):
    url = "https://register.cgmh.org.tw/Progress/V?dept=04&time=1"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 抓取表格資料 (這部分需根據土城醫院網頁結構微調)
        # 這裡提供一個通用的長庚進度抓取邏輯
        rows = soup.find_all('tr')
        result = "🏥 **土城醫院看診進度**\n\n"
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                room = cols[0].text.strip() # 診別
                doctor = cols[1].text.strip() # 醫師
                num = cols[3].text.strip() # 目前號數
                result += f"📍 {room} | {doctor}\n👉 目前號碼：**{num}**\n\n"
        
        if len(rows) < 2:
            result = "目前可能非看診時間，或網頁資料暫時無法讀取。"
            
        bot.reply_to(message, result, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, "查詢失敗，請稍後再試。")

bot.polling()
