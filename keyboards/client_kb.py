from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('Запросить доступ')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)

kb_client.add(b1)
