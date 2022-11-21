import json
import logging
import sched
import time
import atexit
import asyncio

import argparse

import emoji

from parser import find_student_data, update_all_links_cache

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text

# region Чтение аргументов запуска

parser = argparse.ArgumentParser()

parser.add_argument("token", help="Telegram bot API token", type=str)
parser.add_argument("-v", "--verbose", help="Enables debug output", action='store_true')
parser.add_argument("-s", "--skip-updates", help="Enable or disable skipping updates from telegram bot chat",
                    action='store_true')
parser.add_argument("-i", "--interval", help="Updates interval in seconds", default=30, type=int)
parser.add_argument("-l", "--license-agreement-url", help="Url of license agreement", default="", type=str)

args = parser.parse_args()


# endregion

# region настройка логирования
logging.basicConfig(
    level=logging.DEBUG if args.verbose else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
# endregion


bot = Bot(token=args.token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

mode = None

registered_clients = {
    # "122332-12312312-124124 09": {
    #     "telegram_user_id": 1234123123213
    #     "programs": [
    #         {
    #             "program_name": "ИСИТ",
    #             "order": 12
    #         },
    #         {
    #             "program_name": "ИСИТ",
    #             "order": 12
    #         },
    #
    #     ]
    # }
}


# region Обработчики сообщений

@dp.message_handler(commands='start')
async def start(message: types.Message):
    logging.info(message)
    await message.answer(
        'Приветствую! Я умею проверять рейтинговые списки на зачисление в СГУГиТ и отправляю тебе уведомления, когда твоя позиция изменится на каком-либо направлении. Давай начнем, мне нужно знать номер твоего СНИЛС. Чтобы ввести его, нажми соответствующую кнопку',
        reply_markup=reply_keyboard())


@dp.message_handler(Text(equals="Добавить новый СНИЛС"))
async def find_student_info(message: types.Message):
    global mode
    await bot.send_message(message.from_user.id, "Напиши свой снилс", reply_markup=None)
    mode = 'input_snils'


@dp.message_handler(Text(equals="О боте"))
async def about_bot(message: types.Message):
    await bot.send_message(message.from_user.id,
                           "Я умею проверять рейтинговые списки на зачисление в СГУГиТ и отправляю тебе уведомления, когда твоя позиция изменится на каком-либо направлении. \nЛицензионное соглашение: https://staticdocs.petproj.core.borisof.ru/konkurs-visor-license-agreement.html",
                           reply_markup=reply_keyboard())


@dp.message_handler(Text(equals="Узнать свою позицию"))
async def position_check(message: types.Message):
    response = get_formatted_student_data_by_chat_id(message.from_user.id)
    if response is None:
        await message.answer(
            "Мне нужно знать ваш снилс, чтобы начать мониторинг рейтинговых списков. Давай сделаем это",
            reply_markup=reply_keyboard(), parse_mode='Markdown')
        await find_student_info(message)
        return

    await message.answer(response, reply_markup=reply_keyboard(), parse_mode='Markdown')


@dp.message_handler()
async def handle_input(message: types.Message):
    global mode
    if mode != 'input_snils':
        await message.reply("Необходимо написать свой снилс", reply_markup=reply_keyboard())
        return

    snils = message.text
    if not snils.isdigit():
        if not ' ' in snils or not '-' in snils:
            await message.answer('Снилс должен быть числом')
            return

    chat_id = str(message.from_user.id)
    student_data = find_student_data(snils)

    registered_clients[chat_id] = {
        "snils": snils,
        "programs": []
    }

    for key, value in student_data.items():
        registered_clients[chat_id]['programs'].append({
            "program_name": str(key),
            "order": value["order"]
        })

    mode = None

    await bot.send_message(message.from_user.id, get_formatted_student_data_by_chat_id(chat_id), parse_mode='Markdown')


# endregion


def reply_keyboard():
    start_buttons = ["Узнать свою позицию", "Добавить/Изменить СНИЛС", "О боте"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*start_buttons)
    return keyboard


def find_student_data_by_chat_id(chat_id):
    if str(chat_id) not in registered_clients.keys():
        return None

    snils = registered_clients[str(chat_id)]['snils']
    return find_student_data(snils)


def get_formatted_student_data_by_chat_id(chat_id):
    answer = ''

    student_data = find_student_data_by_chat_id(chat_id)
    if student_data is None:
        return None

    for key, value in student_data.items():
        answer += f"*Направление подготовки: {str(key)}*\n " \
                  f":sports_medal: Текущая позиция в списке: {str(value['order'])} \n" \
                  f" {':check_mark_button:  Подлинник предоставлен' if str(value['isOriginals']) else ':cross_mark: Подлинник отсутствует'} \n" \
                  f" {':check_mark_button:  Преимущественное право предоставлено' if value['isAdvantaged'] else ':cross_mark: Преимущественное право не предоставлено'} \n"

    return emoji.emojize(answer)


def cron_task():
    update_all_links_cache()
    # value старая инфа по типу
    for key, value in registered_clients.items():
        # Свежая инфа по типу
        res = find_student_data(value['snils'])
        for old_order_data in value["programs"]:
            program_name = old_order_data["program_name"]
            old_order = old_order_data["order"]
            new_order = res[program_name]["order"]
            if new_order != old_order:
                # Функция, которая оповещает типа об изменении позиции в списке
                # global isOrderChanged
                # isOrderChanged = 'True'
                old_order_data["order"] = new_order
                loop = asyncio.get_event_loop()
                loop.run_until_complete(send_msg(str(key), f"Ваша позиция изменилась с {old_order} на {new_order}"))


async def send_msg(chat_id, msg):
    await bot.send_message(chat_id, msg)


@atexit.register
def exit_handler():
    logging.info("Получена команда на закрытие. Запись в файл текущего состояния...")
    # Открываем файл для записи
    file = open('state.json', 'w')
    jsonStr = json.dumps(registered_clients, ensure_ascii=False, indent=4)
    file.write(jsonStr)
    file.close()
    logging.info("Текущее состояние записано в файл")


def load_state():
    global registered_clients
    try:
        with open('state.json') as json_file:
            registered_clients = json.load(json_file)
            logging.info("Состояние восстановлено")
    except:
        logging.info("Не удалось восстановить состояние")


def main():
    logging.info("Запуск конской хуеты...")
    logging.info("Восстановление предыдущего состояния")
    load_state()
    logging.info("Парсинг текущих рейтинговых списков")
    update_all_links_cache()
    logging.info("Рейтинговые списки получены, запуск бота...")
    s = sched.scheduler(time.time, time.sleep)
    s.enter(int(args.interval), 1, cron_task)
    s.run()
    executor.start_polling(dp, skip_updates=args.skip_updates)
    logging.info("Остановка бота...")


main()
