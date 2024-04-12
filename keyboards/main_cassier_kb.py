from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
	InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client

from datetime import datetime
from datetime import date, timedelta

from handlers import emoji_bot

import emoji


main_cassier_kb = ReplyKeyboardMarkup(resize_keyboard = True)


b1 = KeyboardButton(f'{emoji_bot.em_report_close}Загрузить отчёт')
b2 = KeyboardButton(f'{emoji_bot.em_last_report}Выгрузить прошлый отчёт')
b3 = KeyboardButton(f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц')
b4 = KeyboardButton(f'{emoji_bot.em_salary_button}Рассчитать зарплату сотрудника')
b5 = KeyboardButton(f'{emoji_bot.em_help}Инструкция по загрузке отчёта')


main_cassier_kb.add(b1).insert(b2).row(b3).row(b4).row(b5)
