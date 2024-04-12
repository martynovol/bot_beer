from telnetlib import KERMIT
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from keyboards import kb_client
from handlers import emoji_bot

b1 = KeyboardButton(f'{emoji_bot.em_report_close}Открыть смену')
b2 = KeyboardButton(f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц')

button_storager = ReplyKeyboardMarkup(resize_keyboard = True).add(b1).row(b2)