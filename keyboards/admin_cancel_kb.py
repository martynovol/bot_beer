from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from keyboards import kb_client


b1 = KeyboardButton('Отмена')


button_case_admin_cancel = ReplyKeyboardMarkup(resize_keyboard = True).add(b1)