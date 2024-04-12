
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from handlers import emoji_bot


b1 = KeyboardButton(f'{emoji_bot.em_report_close}Закрыть смену')
b2 = KeyboardButton(f'{emoji_bot.em_last_report}Выгрузить прошлый отчёт')
b3 = KeyboardButton(f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц')
b4 = KeyboardButton(f'{emoji_bot.em_help}Инструкция по загрузке отчёта')
b5 = KeyboardButton(f'📝Добавить списание')
b7 = KeyboardButton(f'📒Локальная ревизия')
b6 = KeyboardButton(f'📔План продаж')


button_cassier = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b6).insert(b5).row(b7).row(b3)