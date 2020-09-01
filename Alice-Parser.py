from MyToken import token
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import telebot
from telebot import types
import threading
import schedule
import time

bot = telebot.TeleBot(token)

current_date = datetime.now().date()
otchet = {}
id_usersname = {}


@bot.message_handler(commands=['start'])
def get_users_id_and_username(message):
    # Если пользователь вызвал Алису в личке, то действует эта конструкция:
    if message.chat.type == 'private':
        chat_id = message.chat.id
        name = message.chat.first_name
        id_usersname.setdefault(chat_id, name)
        otchet.setdefault(name, {})
        bot.send_message(chat_id, f'Привет {name}! Я Алиса, буду проводить для тебя StandUp каждое утро')
    # Если пользователь вызвал Алису в группе, то дейсвтует следующая конструкция:   
    elif message.chat.type == 'supergroup' or message.chat.type == 'group':
        chat_id = message.chat.id
        bot.send_message(chat_id, f'Привет {message.from_user.first_name}, напиши мне в личку')
    
    print(id_usersname)


@bot.message_handler(commands=['Alice', 'change'])
def change_standup(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id 
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn1 = types.KeyboardButton('Да')
        btn2 = types.KeyboardButton('Нет')
        keyboard.add(btn1, btn2)
        msg = bot.send_message(chat_id, 'Привет! Хочешь изменить свой отчет?', reply_markup=keyboard)
        bot.register_next_step_handler(msg, get_change)
    elif message.chat.type == 'supergroup' or message.chat.type == 'group':
        chat_id = message.chat.id 
        bot.send_message(chat_id, f'Привет {message.from_user.first_name}, напиши мне в личку')

def get_change(message):
    chat_id = message.chat.id 
    if message.text == 'Да':
        msg = bot.send_message(chat_id, 'Хорошо! Что вы делали?')
        bot.register_next_step_handler(msg, get_to_do)
    else:
        bot.send_message(chat_id, f'{message.chat.first_name}, не играйтесь!😠')


def start_get_done():
    for id in id_usersname.keys():
        msg = bot.send_message(id, f'Привет! Начнём StandUp.\nЧто вы сделали?')
        bot.register_next_step_handler(msg, get_to_do)
    

def get_to_do(message):
    chat_id = message.chat.id
    otchet[message.chat.first_name]['Done'] = 'Done: ' + message.text 
    msg = bot.send_message(chat_id, f'{message.from_user.first_name}, что вы будете делать?')
    bot.register_next_step_handler(msg, get_problems)
    
def get_problems(message):
    chat_id = message.chat.id 
    otchet[message.chat.first_name]['ToDo'] = 'To Do: ' + message.text
    msg = bot.send_message(chat_id, f'{message.from_user.first_name}, какие сложности у вас возникли?')
    bot.register_next_step_handler(msg, get_bye)
    
def get_bye(message):
    chat_id = message.chat.id 
    otchet[message.chat.first_name]['Problems'] = 'Problems: ' + message.text
    bot.send_message(chat_id, f'{message.from_user.first_name}, спасибо, что отправили отчет😁')
    print(otchet)

def create_otchet():
    file_name = 'otchet.csv'
    with open(file_name, 'a', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\n')
        try:
            for name in otchet.keys():
                writer.writerow( (name, otchet[name]['Done'], otchet[name]['ToDo'], otchet[name]['Problems'], '***') )
        except KeyError:
            print('someone didnt make otchet')

    with open(file_name, 'r', encoding='utf-8') as f:
        reader = f.read()
        return reader


# Данная функция очищает отчет перед каждым новым
def clear_otchet():
    with open('otchet.csv', 'w') as f_clear:
        clearer = f_clear.write('')
        return clearer

def check_otchet():
    with open('otchet.csv', 'r') as f_check:
        checker = f_check.read()
        for id,name in id_usersname.items():
            if otchet[name] == {}:
                bot.send_message(id, 'Просыпайся! Ты ещё не сделал StandUp!')


def get_otchet_to_group():
    chat_id = -1001497031807
    # chat_id = -1001269534952
    bot.send_message(chat_id, f'Отчет:\n {create_otchet()}')
    
    with open('otchet.csv','r') as f_otchet:
        reader = f_otchet.read()
        missed_otchet_list = []
        for name in id_usersname.values():
            if name not in reader:
                missed_otchet_list.append(name)  
        
        if missed_otchet_list == []:
            bot.send_message(chat_id, 'Все сделали StandUp👍🏽') 
        
        else:
            missed_users = ', '.join(missed_otchet_list)
            bot.send_message(chat_id, f'Не сделали StandUp: {missed_users}')
    
    clear_otchet()

schedule.every().day.at("14:13").do(check_otchet)
schedule.every().day.at("14:15").do(get_otchet_to_group)
schedule.every().day.at("14:10").do(start_get_done)

def timer(func, *args):
    threading.Thread(target=func, args=args).start()  

def schedule_():
    while True:
        schedule.run_pending()
        time.sleep(1)

timer(schedule_)

# Parsing part        
@bot.message_handler(commands=['news'])
def start(message):
    chat_id = message.chat.id 
    msg = bot.send_message(chat_id, f'Привет! Готовы к сегодняшним новостям?')
    bot.register_next_step_handler(msg, news)
    
def news(message):
    chat_id = message.chat.id
    try:
        general_url = 'https://kaktus.media/?'
        date_part = 'date=' + str(current_date)
        kaktus_media_url = general_url + date_part


        response = requests.get(kaktus_media_url)
        html = response.text
        soup = BeautifulSoup(html, 'lxml')

        news = soup.find('ul', class_='topic_list').find_all('li', class_='topic_item')
        n = 0
        for new in news[:20]:
            # news_titles
            list_of_news = []
            news_titles = new.find('div', class_='t f_medium').find('a').find('span', class_='n').text
            list_of_news.append(news_titles)
            list_news = '\n'.join(list_of_news)
            n += 1
            msg = bot.send_message(chat_id, f'{n}: {list_news}')
        bot.register_next_step_handler(msg, description)
    except AttributeError:
        bot.send_message(chat_id, f'Новостей пока нет')
        

def description(message):
    chat_id = message.chat.id
    general_url = 'https://kaktus.media/?'
    date_part = 'date=' + str(current_date)
    kaktus_media_url = general_url + date_part

    response = requests.get(kaktus_media_url)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')

    news = soup.find('ul', class_='topic_list').find_all('li', class_='topic_item')
    list_of_descriptions = []
    for new in news[:20]:
        
        # news_description
        news_links = new.find('div', class_='t f_medium').find('a').get('href')
        
        response = requests.get(news_links)
        news_html = response.text
        description_soup = BeautifulSoup(news_html, 'lxml')
        news_descriptions = description_soup.find('div', itemprop="articleBody").text
        list_of_descriptions.append(news_descriptions)
    
    try:
        number_of_news = int(message.text) - 1
        bot.send_message(chat_id, f'{list_of_descriptions[number_of_news]}')
    except:
        number_of_news = int(message.text) - 1
        choice = list_of_descriptions[number_of_news]
        bot.send_message(chat_id, f'{choice[:int(len(choice)/2)]}')
        bot.send_message(chat_id, f'{choice[int(len(choice)/2):]}')


bot.polling()

