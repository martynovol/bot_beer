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
from handlers import inf


def punctuation(mes):
	x = mes
	if len(mes.split(',')) == 2:
		x = ''
		for i in mes:
			if i == ',':
				x += '.'
			else:
				x += i
	return round(float(x), 2)

def check_month(m):
	m = m.split('.')
	return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(m[2]) == 4 
		and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
		and int(m[0])<32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


class FSMFine(StatesGroup):
	person = State()
	fine = State()
	date = State()
	comments = State()


async def cm_start_set_fine(message: types.Message):
	if message.from_user.id not in inf.get_admin_id():
		await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
		return
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	users = inf.get_users()
	available_names = []
	for user in users:
		available_names.append(user[1])
	for name in available_names:
		keyboard.add(name)
	keyboard.add('Отмена')
	await message.reply('Выберите сотрудника:', reply_markup = keyboard)
	await FSMFine.person.set()


async def load_person_fine(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['person'] = message.text
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	keyboard.add('Отмена')
	await FSMFine.next()
	await message.reply('Сумма штрафа:', reply_markup = keyboard)


async def load_fine(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['fine'] = punctuation(message.text)
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	time = str(datetime.now().strftime('%d.%m.%Y'))
	keyboard.add(time)
	keyboard.add('Отмена')
	await FSMFine.next()
	await message.reply('Напишите дату штрафа формата (ДД.ММ.ГГГГ):', reply_markup = keyboard)


async def load_date_fine(message: types.Message, state: FSMContext):
	if check_month(message.text):
		await bot.send_message(message.from_user.id, f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
		return
	date2 = ''
	for i in range(0, 2):
		if len(message.text.split('.')[i]) == 1:
			date2 += '0' + message.text.split('.')[i] + '.'
		else:
			date2 += message.text.split('.')[i] + '.'
	date2 += message.text.split('.')[2]
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	keyboard.add('Отмена')
	async with state.proxy() as data:
		data['date'] = date2
	await FSMFine.next()
	await bot.send_message(message.from_user.id, 'Комментарии к штрафу:', reply_markup=keyboard)


async def load_comments(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['comments'] = message.text
		date1, sum_fine, comment = data['date'], data['fine'], data['comments']
		users = inf.get_users_id()
		uid = int(inf.get_user_id(data['person']))
		if uid in users:
			await bot.send_message(inf.get_user_id(data['person']), f'{emoji_bot.em_main_active}Вам назначен штраф за {date1}:\nСумма: {sum_fine} рублей\nКомментарии: {comment}')
	await bot.send_message(message.from_user.id, 'Штраф успешно назначен', reply_markup=inf.kb(message.from_user.id))
	await sqlite_db.sql_add_fine(state)
	await state.finish()


def register_handlers_fine(dp: Dispatcher):
	dp.register_message_handler(cm_start_set_fine, Text(equals=f'{emoji_bot.em_fine_button}Оштрафовать сотрудника', ignore_case=True), state=None)
	dp.register_message_handler(load_person_fine, state=FSMFine.person)
	dp.register_message_handler(load_fine, state=FSMFine.fine)
	dp.register_message_handler(load_date_fine, state=FSMFine.date)
	dp.register_message_handler(load_comments, state=FSMFine.comments)