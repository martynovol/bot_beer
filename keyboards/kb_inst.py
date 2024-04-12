from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

kb_inst = InlineKeyboardButton(text = 'Instagram', url = 'https://www.instagram.com/dymka.store')
inline_inst = InlineKeyboardMarkup(row_width = 1).add(kb_inst)