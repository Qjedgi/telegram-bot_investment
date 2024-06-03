import telebot
from telebot import types
from tinkoff.invest import Client, PortfolioResponse, RequestError,OrderDirection, OrderType, CandleInterval, HistoricCandle
import pandas as pd
from ta.trend import ema_indicator
from pandas import DataFrame
import os
from datetime import datetime, timedelta
from tinkoff.invest import Client
from dotenv import load_dotenv, find_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
load_dotenv(find_dotenv())
bot= telebot.TeleBot(os.getenv('TOKEN_TG'))
#exchange = os.getenv('TOKEN_TINKOFF')
#acc = os.getenv('TIN_AKK_ID')

@bot.message_handler(commands=["start"])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(m.chat.id, 'Привет! Это дипломная работа на тему "Разработка telegram бота для анализа, обработки и выполнения биржевых операций". Данный бот работает напрямую с API Тинькофф Инвестиций. Для входа на биржу нужен токен. По этой инстукции можно будет его создать <https://github.com/Qjedgi/telegram-bot_investment/blob/main/README.md>. После создания токена отправьте его ответным сообщением.')
    bot.register_next_step_handler(m, authorization)

def authorization(m):
    global token
    token = m.text
    try:
        with Client(token) as client:
            response = client.users.get_accounts()
            if response.accounts:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Новости")
                item2 = types.KeyboardButton("Портфель")
                markup.add(item1,item2)
                bot.send_message(m.chat.id, text='Успешный вход на биржу!', reply_markup=markup)
                delete_images("D:\\Рабочий стол\\bot")
                # Здесь можно добавить логику для работы с ботом после авторизации
            else:
                bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')
    except Exception as e:
        bot.send_message(m.chat.id, 'Ошибка авторизации. Проверьте токен и повторите попытку.')

# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == 'Портфель':
        try:
            #with Client(exchange) as client:
            with Client(token) as client:
                r: PortfolioResponse = client.operations.get_portfolio(account_id=client.users.get_accounts().accounts[0].id)
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
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Анализ")
                item2 = types.KeyboardButton("Покупка")
                item3 = types.KeyboardButton("Продажа")
                item4 = types.KeyboardButton("Назад")
                markup.add(item1).add(item2, item3).add(item4)
                bot.send_message(message.chat.id,
                                 text='Также вы можете проанализировать портфель или докупить или продать ценные бумаги',
                                 reply_markup=markup)
                for p in r.positions:
                    figi = p.figi
                    run(figi)

        except RequestError as e:
            bot.send_message(message.chat.id, str(e))

    elif message.text.strip() == 'Анализ':
        bot.register_next_step_handler(message, main)
        file1 = open('summary_report.pdf', 'rb')
        bot.send_document(message.chat.id, file1)
        file1.close()
        bot.register_next_step_handler(message, images_to_pdf)
        file = open('output.pdf', 'rb')
        bot.send_document(message.chat.id, file)
        file.close()

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
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Новости")
        item2 = types.KeyboardButton("Портфель")
        markup.add(item1, item2)
        bot.send_message(message.chat.id, 'Вы вернулись назад',reply_markup=markup)

def main(token):
    with Client(token) as client:
        accounts =client.users.get_accounts()
        operations = []

        for account in accounts.accounts:
            operations_response = client.operations.get_operations(
                account_id=account.id,
                from_=datetime(2023, 9, 1),
                to=datetime.now()
            )

            for operation in operations_response.operations:
                operations.append({
                    "type": operation.type,
                    "payment": operation.payment.units + operation.payment.nano / 10 ** 9
                })

        # Группировка и сводка операций по типу
        summary = {}
        for operation in operations:
            if operation["type"] not in summary:
                summary[operation["type"]] = 0
            summary[operation["type"]] += operation["payment"]

        # Подготовка содержимого PDF
        story = []
        styles = getSampleStyleSheet()
        russian_style = ParagraphStyle(name='Russian', fontName='Arial', fontSize=12, leading=15)
        for key, value in summary.items():
            story.append(Paragraph(f"<b>{key}:</b><br/>{value:.2f}", russian_style))
        story.append(Paragraph("<b>Итого:</b><br/>" + str(sum(summary.values())), russian_style))

        # Генерация отчета PDF
        doc = SimpleDocTemplate("summary_report.pdf", pagesize=letter)
        doc.build(story)
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
                account_id=client.users.get_accounts().accounts[0].id,
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
                account_id=client.users.get_accounts().accounts[0].id,
                direction=OrderDirection.ORDER_DIRECTION_SELL,
                order_type=OrderType.ORDER_TYPE_MARKET
            )
            bot.send_message(message.chat.id, 'Вы успешно продали ценную бумагу!')
    except RequestError as e:
        print(str(e))

def run(figi):
    try:
        with Client(token) as client:
            r = client.market_data.get_candles(
                figi=figi,
                from_=datetime.utcnow() - timedelta(days=7),
                to=datetime.utcnow(),
                interval=CandleInterval.CANDLE_INTERVAL_HOUR  # см. utils.get_all_candles
            )
            # print(r)

            df = create_df(r.candles)
            # https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.ema_indicator
            df['ema'] = ema_indicator(close=df['close'], window=9)

            #print(df[['time', 'close', 'ema']].tail(30))
            ax = df.plot(x='time', y='close')
            df.plot(ax=ax, x='time', y='ema')
            fig = ax.get_figure()
            fig.savefig(f'{figi}.png')

    except RequestError as e:
        print(str(e))



from fpdf import FPDF

def images_to_pdf(directory, pdf_filename):
    pdf = FPDF()
    for i, file in enumerate(os.listdir(directory)):
        if file.endswith(".png"):
            pdf.add_page()
            pdf.set_font("Arial", size=12)  # Установка шрифта и размера
            pdf.image(os.path.join(directory, file), x=10, y=10, w=180, h=180)  # Размещение изображения в верхней части страницы
            prefix = "Image "
            pdf.cell(0, 30, txt=f"{prefix}{file}", ln=True, align="C")
    pdf.output(pdf_filename, "F")

def create_df(candles: [HistoricCandle]):
    df = DataFrame([{
        'time': c.time,
        'volume': c.volume,
        'open': money(c.open),
        'close': money(c.close),
        'high': money(c.high),
        'low': money(c.low),
    } for c in candles])

    return df
def money(a):
    return a.units+a.nano/1e9 # нано -> 10 в -9 степени

def delete_images(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            os.remove(os.path.join(directory, filename))
# пример использования

#units - Целая часть суммы, может быть отрицательным числом
#nano - Дробная часть суммы, может быть отрицательным числом
def main():
    with Client(token) as client:
        accounts =  client.users.get_accounts()
        operations = []
        for account in accounts.accounts:
            operations_response = client.operations.get_operations(
              account_id=account.id,
              from_=datetime(2023, 9, 1),
                to=datetime.now()
            )
            for operation in operations_response.operations:
                operations.append({
                    "type": operation.type,
                    "payment": operation.payment.units + operation.payment.nano / 10**9
                })
        # Группировка и суммирование операций по типу
        summary = {}
        for operation in operations:
            if operation["type"] not in summary:
                summary[operation["type"]] = 0
            summary[operation["type"]] += operation["payment"]
        # Вывод данных в консоль
        for key, value in summary.items():
            print(f"{key}: {value}")
        # Общий итог
        total = sum(summary.values())
        print(f"Total: {total}")

bot.infinity_polling()
#sosihui # lyalyatopolya




