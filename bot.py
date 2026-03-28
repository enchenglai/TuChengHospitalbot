import requests
from bs4 import BeautifulSoup
import telebot

TOKEN = '8691465383:AAFu5Gewknc4xH2nFe3hl9GEghu9HxSsLJQ'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['check'])
def check_progress(message):
    url = "https://register.cgmh.org.tw/Progress/V?dept=04&time=1"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    # 這裡需根據網頁實際 HTML 結構選取進度文字
    progress_info = soup.find('table').text # 範例代碼
    bot.reply_to(message, f"目前土城醫院看診進度：\n{progress_info}")

bot.polling()