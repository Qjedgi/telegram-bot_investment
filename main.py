import telebot
from tinkoff.invest import Client, PortfolioResponse, RequestError, PositionsResponse, PortfolioPosition
import os
from dotenv import load_dotenv, find_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable

load_dotenv(find_dotenv())
bot= telebot.TeleBot(os.getenv('TOKEN_TG'))
exchange = os.getenv('TOKEN_TINKOFF')
acc = os.getenv('TIN_AKK_ID')

@bot.message_handler(commands=['start'])
def main (message):
    bot.send_message(message.chat.id,'Диплом "РАЗРАБОТКА TELEGRAM БОТА ДЛЯ АНАЛИЗА, ОБРАБОТКИ И ВЫПОЛНЕНИЯ БИРЖЕВЫХ ОПЕРАЦИЙ"')
@bot.message_handler(commands=['news'])
def main (message):
    bot.send_message(message.chat.id,'press f')

@bot.message_handler(commands=['buy'])
def main (message):
    bot.send_message(message.chat.id,'5000 ')

@bot.message_handler(commands=['sale'])
def main(message):
    bot.send_message(message.chat.id, 'sale')

def money(a):
    return a.units+a.nano/1e9 # нано -> 10 в -9 степени
#units - Целая часть суммы, может быть отрицательным числом
#nano - Дробная часть суммы, может быть отрицательным числом

@bot.message_handler(commands=['bag'])
def main(message):
        try:
            with Client(exchange) as client:
                r: PortfolioResponse = client.operations.get_portfolio(account_id=acc)
                df = pd.DataFrame([{
                'figi': p.figi,
                'qnty': money(p.quantity),
                'expected_yield': money(p.expected_yield), # Текущая рассчитанная доходность
                'instrument_type': p.instrument_type, # Тип инструмента
                'sr': money(p.average_position_price),
                'cost' : format((money(p.average_position_price) * money(p.quantity)) + money(p.expected_yield) + (money(p.current_nkd)*money(p.quantity)),'.2f')
                } for p in r.positions])
                # Создавние PrettyTable объекта
                pt_table = PrettyTable()
                # Добьавляются названия колонок из датафрейма
                pt_table.field_names = df.columns.tolist()
                # добавляются строчки
                for i, row in df.iterrows():
                    pt_table.add_row(row.tolist())
                bot.send_message(message.chat.id, pt_table)
        except RequestError as e:
            bot.send_message(message.chat.id, e)
        # Получение уникальных типов инструментов и их количество
        instrument_types = df['instrument_type'].unique()
        counts = [len(df[df['instrument_type'] == t]) for t in instrument_types]
        # Создание круговой диаграммы
        plt.pie(counts, labels=instrument_types,autopct='%1.1f%%')
        # Сохранение плота в png и отправка в чат
        plt.savefig('bag_share', bbox_inches='tight')
        bot.send_photo(message.chat.id, photo=open('bag_share.png', 'rb'))
        # Удаление файла после отправки
        file_path = 'bag_share.png'
        if os.path.isfile(file_path):
            os.remove(file_path)
            print('File deleted.')
        else:
            print('File does not exist.')

bot.infinity_polling()





