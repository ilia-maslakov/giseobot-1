from calendar import week
import re
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
    def __init__(self, weeklessons, this_week : date = date.today(), cday : str = '', cdate: str = ''):
        self.weeklessons = weeklessons
        self.selectday = cday
        self.selectdate = cdate
        self.this_week = this_week

#bot_data = []

@bot.message_handler(commands=['start'])
def start(message):
    reg = check_registration(message.from_user.id)
    if reg['registred'] == 'true':
        global bot_data

        diary = get_diary(reg, date.today())
        bot_data = BotData(diary['weekDays'])
        drow_buttons_days(message)

@bot.message_handler(content_types=['text'])
def func(message):
    tmpday, tmpdate = day_from_message(message.text)
    legal_command = False
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEEstRietZXy3xPJGFwxIM7Z6dBzNMsWAACCAADwDZPE29sJgveGptpJAQ')
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
        if message.text == 'Предыдущая неделя':
            bot_data.this_week = minus_week(bot_data.this_week)
            reg = check_registration(message.from_user.id)
            diary = get_diary(reg, bot_data.this_week)
            bot_data.weeklessons = diary['weekDays']
            drow_buttons_days(message)
            return

        if message.text == 'Следующая неделя':
            bot_data.this_week = plus_week(bot_data.this_week)
            reg = check_registration(message.from_user.id)
            diary = get_diary(reg, bot_data.this_week)
            bot_data.weeklessons = diary['weekDays']
            drow_buttons_days(message)
            return
            
        if message.text == 'Текущая неделя':
            bot_data.this_week = date.today()
            reg = check_registration(message.from_user.id)
            diary = get_diary(reg, bot_data.this_week)
            bot_data.weeklessons = diary['weekDays']
            drow_buttons_days(message)
            return

        if message.text == 'Выбор дня':
            reg = check_registration(message.from_user.id)
            diary = get_diary(reg, bot_data.this_week)
            bot_data.weeklessons = diary['weekDays']
            drow_buttons_days(message)
            return

        if bot_data.selectdate == '':
            bot.send_message(message.chat.id, text='Не коректная комманда! Выберите день недели')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEEs0Fiet2fnuOjnE9XlPjs5G9_jGrmOgACLwMAAm2wQgNGjkrdcnqC4SQE')
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
                        bot.send_animation(message.chat.id,r'https://i.pinimg.com/originals/a5/e3/81/a5e381d08ef1b8f964b24672b0b0a9f9.gif')
                else:   
                    if legal_command == False:
                        bot.send_message(message.chat.id, text = 'Не коректная комманда! Выберите урок')    
                        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEEs0Fiet2fnuOjnE9XlPjs5G9_jGrmOgACLwMAAm2wQgNGjkrdcnqC4SQE')
                        
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

def minus_week(this_week):
    this_week -= timedelta(days=7)
    return this_week

def plus_week(this_week):
    this_week += timedelta(days=7)
    return this_week

def get_diary(reg, ddate):
    manager = Manager (login=reg['username'], password=reg['password'])
    start_date = startWeek(ddate)
    end_date = endWeek(start_date)
    diary = manager.getDiary (start=dateToSecond(start_date), end=dateToSecond(end_date))
    return diary

def drow_buttons_days(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for wday in bot_data.weeklessons:
            day = wday['date']
            c = datetime.fromisoformat(day)
            button = types.KeyboardButton(weekdays[c.weekday()] + ' (' + day + ')' )
            markup.add(button)
        
        #markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons=['Предыдущая неделя','Текущая неделя','Следующая неделя']
        markup.add(*buttons)

        start_date = startWeek(bot_data.this_week)
        end_date = endWeek(start_date)
        bot.send_message(message.chat.id, text='Неделя с \n' + str(start_date).split(' ')[0] + ' по ' + str(end_date).split(' ')[0], reply_markup=markup)

if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

