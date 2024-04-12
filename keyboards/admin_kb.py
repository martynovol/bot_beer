from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
	InlineKeyboardButton

from create_bot import dp, bot
from handlers import emoji_bot
from handlers import inf

import emoji

b1 = KeyboardButton('Отчёты')
b2 = KeyboardButton('Зарплаты')

async def menu_reports_admin(message: types.Message):
	if message.from_user.id in inf.get_mod_id():
		b1 = KeyboardButton(f'{emoji_bot.em_report_close}Открыть смену')
		b2 = KeyboardButton(f'{emoji_bot.em_report_close}Закрыть смену')
		b3 = KeyboardButton(f'{emoji_bot.em_report_for_day}Выгрузить отчёт за день')
		b4 = KeyboardButton(f'{emoji_bot.em_report_for_month}Выгрузить выручку за месяц')
		b5 = KeyboardButton(f'{emoji_bot.em_report_for_diap}Выгрузить диапазон')
		b6 = KeyboardButton(f'{emoji_bot.em_help}Инструкция по загрузке отчёта')
		b7 = KeyboardButton('Загрузить данные в таблицу')
		b8 = KeyboardButton('Ссылка на таблицу')
		b10 = KeyboardButton(f'{emoji_bot.em_report_load_zamena}Провести замену')
		b9 = KeyboardButton('Вернуться')
		keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(b1).insert(b2).row(b3).insert(b4).insert(b5).row(b6).insert(b7).insert(b8).row(b10).row(b9)
		await bot.send_message(message.from_user.id,'Вы перешли в меню <<Отчёты>>', reply_markup = keyboard)
	else:
		b1 = KeyboardButton(f'{emoji_bot.em_report_close}Открыть смену')
		b2 = KeyboardButton(f'{emoji_bot.em_report_close}Открыть смену управляющего')
		b3 = KeyboardButton(f'{emoji_bot.em_report_close}Закрыть смену')
		b4 = KeyboardButton(f'{emoji_bot.em_report_for_day}Выгрузить отчёт за день')
		b5 = KeyboardButton(f'{emoji_bot.em_report_for_diap}Выгрузить диапазон')
		b7 = KeyboardButton('Загрузить данные в таблицу')
		b8 = KeyboardButton('Ссылка на таблицу')
		keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(b1).insert(b2).row(b3).insert(b4).row(b5).insert(b7).row(b8)
		await bot.send_message(message.from_user.id,'Вы перешли в меню <<Отчёты>>', reply_markup = keyboard)

async def menu_salary_admin(message: types.Message):
	b1 = KeyboardButton(f'{emoji_bot.em_salary_button}Рассчитать зарплату сотрудника')
	b2 = KeyboardButton('Назначить ставку сотруднику')
	b3 = KeyboardButton(f'{emoji_bot.em_fine_button}Оштрафовать сотрудника')
	b4 = KeyboardButton(f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц')
	b5 = KeyboardButton(f'Начислить зарплату')
	b6 = KeyboardButton(f'Долги по выплатам')
	b7 = KeyboardButton('Вернуться')
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True).add(b1).insert(b2).row(b3).insert(b4).row(b5).insert(b6).row(b7)
	await bot.send_message(message.from_user.id,'Вы перешли в меню <<Зарплаты>>', reply_markup = keyboard)


button_case_admin = ReplyKeyboardMarkup(resize_keyboard = True).add(b1).add(b2)

def register_handlers_admin_kb(dp: Dispatcher):
	dp.register_message_handler(menu_reports_admin, Text(equals='Отчёты', ignore_case=True), state=None)
	dp.register_message_handler(menu_reports_admin, Text(equals='Зарплаты', ignore_case=True), state=None)
