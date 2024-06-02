import requests
import telebot
from telebot import types
from tinkoff.invest import Client, PortfolioResponse, RequestError,OrderDirection, OrderType
import os
from dotenv import load_dotenv, find_dotenv
import pandas as pd
from datetime import datetime
load_dotenv(find_dotenv())
bot= telebot.TeleBot(os.getenv('TOKEN_TG'))
#exchange = os.getenv('TOKEN_TINKOFF')
acc = os.getenv('TIN_AKK_ID')

@bot.message_handler(commands=["start"])
def start(m):
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Новости")
        item2 = types.KeyboardButton("Портфель")
        markup.add(item1, item2)
        bot.send_message(m.chat.id,'Привет! Это дипломная работа на тему "Разработка telegram бота для анализа, обработки и выполнения биржевых операций". Данный бот работает напрямую с API Тинькофф Инвестиций.',  reply_markup=markup)


@bot.message_handler(commands=["start"])
def start(m):
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Авторизация")
        markup.add(item1,)
        bot.send_message(m.chat.id,'Привет! Это дипломная работа на тему "Разработка telegram бота для анализа, обработки и выполнения биржевых операций". Данный бот работает напрямую с API Тинькофф Инвестиций. Для входа на биржу нужен токен. По этой инстукции можно будет его создать <> . После создания токена отправьте его ответным сообщением. ',  reply_markup=markup)
        bot.register_next_step_handler(m, authorization)
def authorization(m):
    global token
    token = m.text
    try:
        with Client(token) as client:
            response = client.users.get_accounts()
            if response.accounts:
                account_id = response.accounts[0].id
                bot.send_message(m.chat.id, f'Успешный вход на биржу! Ваш ID аккаунта: {account_id}')
                # Здесь можно добавить логику для работы с ботом после авторизации
            else:
                bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')
    except Exception as e:
        bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')

# @bot.message_handler(commands=["start"])
# def start(m):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     item1 = types.KeyboardButton("Авторизация")
#     markup.add(item1,)
#     bot.send_message(m.chat.id, 'Привет! Это дипломная работа на тему "Разработка telegram бота для анализа, обработки и выполнения биржевых операций". Данный бот работает напрямую с API Тинькофф Инвестиций. Для входа на биржу нужен токен. По этой инстукции можно будет его создать <> . После создания токена отправьте его ответным сообщением.', reply_markup=markup)
#     bot.register_next_step_handler(m, authorization)
#
# import asyncio
# from tinkoff.invest import AsyncClient
#
# async def authorization(m):
#     global token
#     token = m.text
#     try:
#         async with AsyncClient(token) as client:
#             response = await client.users.get_accounts()
#             if response.accounts:
#                 account_id = response.accounts[0].id
#                 bot.send_message(m.chat.id, f'Успешный вход на биржу! Ваш ID аккаунта: {account_id}')
#                 # Здесь можно добавить логику для работы с ботом после авторизации
#             else:
#                 bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')
#     except Exception as e:
#         bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')

import asyncio
# @bot.message_handler(commands=["start"])
# async def start(m):
#     # markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     # item1 = types.KeyboardButton("Авторизация")
#     # markup.add(item1)
#     bot.send_message(m.chat.id, 'Привет! Это дипломная работа на тему "Разработка telegram бота для анализа, обработки и выполнения биржевых операций". Данный бот работает напрямую с API Тинькофф Инвестиций. Для входа на биржу нужен токен. По этой инстукции можно будет его создать <>. После создания токена отправьте его ответным сообщением. ')
#     bot.register_next_step_handler(m, authorization)
#
# async def authorization(m):
#     global token
#     token = m.text
#     try:
#         async with Client(token) as client:
#             response = await client.users.get_accounts()
#             if response.accounts:
#                 account_id = response.accounts[0].id
#                 bot.send_message(m.chat.id, f'Успешный вход на биржу! Ваш ID аккаунта: {account_id}')
#                 # Здесь можно добавить логику для работы с ботом после авторизации
#             else:
#                 bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')
#     except Exception as e:
#         bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')

# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == 'Портфель':
        try:
            #with Client(exchange) as client:
            with Client(token) as client:
                r: PortfolioResponse = client.operations.get_portfolio(account_id=acc)
                df = pd.DataFrame([
                    {
                        'figi': p.figi,
                        'qnty': money(p.quantity),
                        'sr': money(p.average_position_price),
                        'cost': format(
                            (money(p.average_position_price) * money(p.quantity)) + money(p.expected_yield) + (
                                    money(p.current_nkd) * money(p.quantity)), '.2f')
                    } for p in r.positions
                ])
                # Convert DataFrame to dictionary
                d = df.to_dict(orient='records')
                # Format output
                output = '\n'.join(
                    f'{i + 1}. figi={row["figi"]}\n    qnty={row["qnty"]}\n     sr  = {row["sr"]}\n    cost  = {row["cost"]}'
                    for
                    i, row in enumerate(d))
                bot.send_message(message.chat.id, output)
        except RequestError as e:
            bot.send_message(message.chat.id, str(e))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Анализ")
        item2 = types.KeyboardButton("Покупка")
        item3 = types.KeyboardButton("Продажа")
        item4 = types.KeyboardButton("Назад")
        markup.add(item1).add(item2,item3).add(item4)
        bot.send_message(message.chat.id, text='Также вы можете проанализировать портфель или докупить или продать ценные бумаги', reply_markup=markup)
    elif message.text.strip() == 'Анализ':
        pass
    elif message.text.strip() == 'Новости':
        # парсер новостей из сайтов и каналов , ссылка на канал
        markup = telebot.types.InlineKeyboardMarkup()
        button = telebot.types.InlineKeyboardButton(text="Перейти в канал", url='https://t.me/zval_kiwi_news')
        markup.add(button)
        bot.send_message(message.chat.id, "Нажмите на кнопку, чтобы перейти в канал с новостями", reply_markup=markup)
    elif message.text.strip() == 'Покупка':
        bot.send_message(message.chat.id, 'Введите figi необходимой бумаги')
        bot.register_next_step_handler(message, figi_buy)
    elif message.text.strip() == 'Продажа':
        bot.send_message(message.chat.id, 'Введите figi необходимой бумаги')
        bot.register_next_step_handler(message, figi_sale)
    elif message.text.strip() == 'Назад':
        bot.register_next_step_handler(message, start(message))
def figi_buy(message):
    global figi_value
    figi_value = message.text
    bot.send_message(message.chat.id, 'Введите количество')
    bot.register_next_step_handler(message, qnty_buy)
def qnty_buy(message):
    global qnty_value
    qnty_value = message.text
        # Теперь вы можете использовать figi_value и qnty_value для дальнейшей обработки
    print(f'figi: {figi_value}, qnty: {qnty_value}')

    try:
        with Client(token) as client:
                # Рыночная, без указания цены (по лучшей доступной для объема)
            r = client.orders.post_order(
                order_id=str(datetime.utcnow().timestamp()),
                figi=figi_value,
                quantity=int(qnty_value),
                account_id=acc,
                direction=OrderDirection.ORDER_DIRECTION_BUY,
                order_type=OrderType.ORDER_TYPE_MARKET
                )
            bot.send_message(message.chat.id, 'Вы успешно купили ценную бумагу!')
    except RequestError as e:
        print(str(e))
        bot.send_message(message.chat.id, 'УПС! Ошибка')
def figi_sale(message):
    global figi_value
    figi_value = message.text
    bot.send_message(message.chat.id, 'Введите количество')
    bot.register_next_step_handler(message, qnty_sale)

def qnty_sale(message):
    global qnty_value
    qnty_value = message.text
    # Теперь вы можете использовать figi_value и qnty_value для дальнейшей обработки
    print(f'figi: {figi_value}, qnty: {qnty_value}')

    try:
        with Client(token) as client:
            # Рыночная, без указания цены (по лучшей доступной для объема)
            r = client.orders.post_order(
                order_id=str(datetime.utcnow().timestamp()),
                figi=figi_value,
                quantity=int(qnty_value),
                account_id=acc,
                direction=OrderDirection.ORDER_DIRECTION_SELL,
                order_type=OrderType.ORDER_TYPE_MARKET
            )
            bot.send_message(message.chat.id, 'Вы успешно продали ценную бумагу!')
    except RequestError as e:
        print(str(e))

def money(a):
    return a.units+a.nano/1e9 # нано -> 10 в -9 степени
#units - Целая часть суммы, может быть отрицательным числом
#nano - Дробная часть суммы, может быть отрицательным числом
bot.infinity_polling()
#sosihui # lyalyatopolya




