import json
import sched
import time
import atexit

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text

from main import find_student_data, update_all_links_cache

API_TOKEN = '5456787225:AAHYLVfmLl0VJMciHVtssHqX1FzLp2iwsno'

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

mode = None
# isOrderChanged = None

registered_clients = {
    # "122332-12312312-124124 09": {
    #     "telegram_user_id": 1234123123213
    #     "programs": [
    #         {
    #             "program_name": "ИСИТ ЕПТА",
    #             "order": 12
    #         },
    #         {
    #             "program_name": "ИСИТ ЕПТА",
    #             "order": 12
    #         },
    #
    #     ]
    # }
}


@dp.message_handler(commands='start')
async def start(message: types.Message):
    start_buttons = ["Узнать свою позицию", "Добавить новый СНИЛС", "О боте"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer('Готов к труду и обороне', reply_markup=keyboard)


@dp.message_handler(Text(equals="Добавить новый СНИЛС"))
async def find_student_info(message: types.Message):
    global mode
    await bot.send_message(message.from_user.id, "Напиши свой снилс")
    mode = 'input_snils'
    # await message.answer("Подожди секунду...")


@dp.message_handler(Text(equals="Узнать свою позицию"))
async def position_check(message: types.Message):
    current_user_position = registered_clients[message.from_user.id]
    snils = current_user_position['snils']
    student_info = find_student_data(snils)
    response = get_position_message(student_info)
    await message.reply(response)


# dp.message_handler()
# async def update_order(message: types.Message):
#     if isOrderChanged == 'True':
#         await message.answer(f"Ваша позиция изменилась с {cron_task().old_order} на {cron_task().new_order}")

@dp.message_handler()
async def handle_input(message: types.Message):
    global mode
    if mode != 'input_snils':
        return

    snils = message.text
    if not snils.isdigit():
        if not ' ' in snils or not '-' in snils:
            await message.answer('Снилс должен быть числом')
            return

    res = find_student_data(snils)
    info = ""

    registered_clients[message.from_user.id] = {
        "snils": snils
    }

    programs_array = []

    for key, value in res.items():
        info += "Направление подготовки: " + str(key) + "\n Позиция в списке: " + str(
            value["order"]) + "\n Подлинник: " + str(value["isOriginals"] == 'Да')

        programs_array.append({
            "program_name": str(key),
            "order": value["order"]
        })

        await bot.send_message(message.from_user.id, info)

    registered_clients[message.from_user.id]['programs'] = programs_array


def cron_task():
    update_all_links_cache()
    # value старая инфа по типу
    for key, value in registered_clients.items():
        # Свежая инфа по типу
        res = find_student_data(key)
        for old_order_data in value["programs"]:
            program_name = old_order_data["program_name"]
            old_order = old_order_data["old_order"]
            new_order = res[program_name]["order"]
            if new_order != old_order:
                # Функция, которая оповещает типа об изменении позиции в списке
                # global isOrderChanged
                # isOrderChanged = 'True'
                bot.send_message(key, f"Ваша позиция изменилась с {old_order} на {new_order}")


def get_position_message(student_info):
    info = ''
    for key, value in student_info.items():
        info += "Направление подготовки: " + str(key) + "\n Позиция в списке: " + str(
            value["order"]) + "\n Подлинник: " + str(value["isOriginals"] == 'Да')

    return info


@dp.message_handler()
async def file_used_id(message: types.Message, user, snils):
    # Открываем файл для записи
    file = open(str(snils) + '.txt', 'w')
    # Записываем
    user = message.from_user.id
    file.write("User: {}, id: {}\n".format(user, snils))
    # Закрываем файл
    file.close()


def exit_handler():
    # Открываем файл для записи
    file = open('huy.json', 'w')
    jsonStr = json.dumps(registered_clients, ensure_ascii=False, indent=4)
    file.write(jsonStr)
    file.close()


def main():
    atexit.register(exit_handler)
    executor.start_polling(dp, skip_updates=True)
    update_all_links_cache()
    s = sched.scheduler(time.time, time.sleep)
    s.enter(5, 1, cron_task)
    s.run()


main()
