from telnetlib import KERMIT
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from keyboards import kb_client
from handlers import emoji_bot


b1 = KeyboardButton(f'{emoji_bot.em_report_close}Открыть смену')
b2 = KeyboardButton(f'{emoji_bot.em_last_report}Выгрузить прошлый отчёт')
b3 = KeyboardButton(f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц')
b4 = KeyboardButton(f'{emoji_bot.em_report_load_zamena}Провести замену')
#b5 = KeyboardButton(f'{emoji_bot.em_help}Инструкция по загрузке отчёта')

#b7 = KeyboardButton('Заменить кассира')
button_cassier = ReplyKeyboardMarkup(resize_keyboard = True).add(b1).insert(b2).row(b3).row(b4)