from calendar import week
from tkinter import Button
from config import TG_MASTER_KEY, GISEO_LOGIN, GISEO_PASSWORD
from libgiseo import Manager
import telebot
from telebot import types 
from datetime import datetime, timedelta, date

weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

bot = telebot.TeleBot(TG_MASTER_KEY)
#bot.send_message(message.chat.id, text='Добро пожаловать', parse_mode='Markdown')
#global bot_data

class BotData:
    def __init__(self, weeklessons, cday : str = '', cdate: str = ''):
        self.weeklessons = weeklessons
        self.selectday = cday
        self.selectdate = cdate

#bot_data = []

@bot.message_handler(commands=['start'])
def start(message):

    reg = check_registration(message.from_user.id)
    if reg['registred'] == 'true':
        global bot_data
        manager = Manager (login=reg['username'], password=reg['password'])
        #start_date = startWeek(date.today())
        start_date = startWeek(date(2022, 5, 3))
        end_date = endWeek(start_date)
        diary = manager.getDiary (start=dateToSecond(start_date), end=dateToSecond(end_date))
        
        bot_data = BotData(diary['weekDays'])
    
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for wday in bot_data.weeklessons:
            day = wday['date']
            c = datetime.fromisoformat(day)
            button = types.KeyboardButton(weekdays[c.weekday()] + ' (' + day + ')' )
            markup.add(button)
        button = types.KeyboardButton('Вернуться к выбору недели')
        markup.add(button)
        bot.send_message(message.chat.id, text='Неделя с ' + str(start_date) + ' по ' + str(end_date), reply_markup=markup)

# from aiogram.dispatcher.filters import Text
@bot.message_handler(commands=['Вернуться к выбору недели'])
def with_puree(message: types.Message):
    message.reply("Отличный выбор!")

@bot.message_handler(content_types=['text'])
def func(message):
    tmpday, tmpdate = day_from_message(message.text)
    legal_command = False

    if 'bot_data' not in globals():
        start(message)
        return

    #bot.send_message(message.chat.id, text=tmpdate)
    if check_day(tmpday):
        legal_command = True
        bot_data.selectday = tmpday
        bot_data.selectdate = tmpdate 
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        printedText = ''
        for wday in bot_data.weeklessons:
            if wday['date'] == bot_data.selectdate:
                for l in wday['lessons']:
                    printedText += '**' + l['subjectName'] + '**' 
                    mark = ' '
                    if 'assignments' in  l:
                        for a in l['assignments']:
                            if 'mark' in a:
                                current_mark = str(a['mark']['mark'])
                                if current_mark == 'None':
                                     current_mark = '🔴' 
                                if mark != ' ':
                                    mark += '  /  ' + current_mark
                                else:
                                    mark += ' ' + current_mark
                    if mark != ' ':
                        printedText += '   — ' + mark + ' \n' 
                    else: 
                        printedText += ' \n' 

                    button = types.KeyboardButton(l['subjectName'])
                    markup.add(button)
                button = types.KeyboardButton('Выбор дня')
                markup.add(button)
        #bot.send_message(message.chat.id, text=printedText, parse_mode='Markdown')
        bot.send_message(message.chat.id, text=printedText, reply_markup=markup, parse_mode='Markdown')
    else:
        if message.text == 'Вернуться к выбору недели':
            select_week(message)
            return

        if message.text == 'Выбор дня':
            start(message)
            return

        if bot_data.selectdate == '':
            bot.send_message(message.chat.id, text='Не коректная комманда! Выберите день недели')
            return

        for wday in bot_data.weeklessons:
            if wday['date'] == bot_data.selectdate:
                for l in wday['lessons']:
                    if l['subjectName'] == message.text:
                        if 'assignments' in  l:
                            for a in l['assignments']:
                                legal_command = True
                                bot.send_message(message.chat.id, text=a['assignmentName'])
                        else:
                            legal_command = True
                            bot.send_message(message.chat.id, text='💪🕺Не задано🕺💪', parse_mode='MarkdownV2')
                else:
                    if legal_command == False:
                        bot.send_message(message.chat.id, text = 'Не коректная комманда! Выберите урок')    

def check_registration(user_id):
    return { 'registred': 'true', 'cid': '2', 'sid': '11', 'pid': '-168', 'cn': '168', 'sft': '2', 'scid': '8', 'username': GISEO_LOGIN, 'password': GISEO_PASSWORD }

def check_day(day):
    for i in weekdays:
        if i == day.replace(' ', ''):
            return True
    return False

def day_from_message(msg):
    m = msg.replace(')', '(')
    res = m.split('(')
    if len(res) > 1:
        return res[0], res[1]
    else:
        return '', ''

def startWeek(ddate):
    ret = datetime.strptime('%04d-%02d-1' % (ddate.year, ddate.isocalendar()[1]), '%Y-%W-%w')
    if date(ddate.year, 1, 4).isoweekday() > 4:
        ret -= timedelta(days=7)
    return ret

def endWeek(ddate):
    ret=startWeek(ddate)
    return (ret + timedelta(days=6))

def dateToSecond(ddate):
    return (ddate.date() - date(1970, 1, 1)).total_seconds()

def select_week(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons=['Предыдущая неделя','Текущая неделя','Следующая неделя']
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, text='Выбор недели', reply_markup=keyboard)

if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

