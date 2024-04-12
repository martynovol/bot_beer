from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
	InlineKeyboardButton

from create_bot import dp, bot
import sqlite3 as sq
from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
import asyncio


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


class FSMInvoices(StatesGroup):
	person = State()
	point = State()
	provider_invoices = State()
	date_invoices = State()
	sum_invoices = State()
	id_invoices = State()
	photo_invoices = State()


async def cm_start_load_invoices(message: types.Message):
	if True:
		await bot.send_message(message.from_user.id, 'Функция в разработке')
		return
	if message.from_user.id not in inf.get_users_id():
		await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
		return
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	available_points = inf.get_name_shops()
	for point in available_points:
		keyboard.add(point)
	keyboard.add('Отмена')
	await message.reply('Выберите точку:', reply_markup = keyboard)
	await FSMInvoices.point.set()


async def load_point(message: types.Message, state: FSMContext):
	available_points = inf.get_name_shops()
	if message.text not in available_points:
		await bot.send_message(message.from_user.id, 'Выберите точку из предложенных')
		return
	async with state.proxy() as data:
		data['person'] = inf.get_name(message.from_user.id)
		data['point'] = message.text
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	keyboard.add('Отмена')
	await FSMInvoices.next()
	await message.reply('Впишите поставщика:', reply_markup = keyboard)


async def load_provider(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['provider_invoices'] = message.text
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	time = str(datetime.now().strftime('%d.%m.%Y'))
	keyboard.add(time)
	keyboard.add('Отмена')
	await FSMInvoices.next()
	await message.reply('Впишите дату по накладной:', reply_markup = keyboard)


async def load_date_invoices(message: types.Message, state: FSMContext):
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
	async with state.proxy() as data:
		data['date_invoices'] = date2
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	keyboard.add('Отмена')
	await FSMInvoices.next()
	await message.reply('Впишите общую сумму товара по накладной:', reply_markup = keyboard)


async def load_sum_invoices(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['sum_invoices'] = punctuation(message.text)
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	keyboard.add('Отмена')
	await FSMInvoices.next()
	await message.reply('Впишите номер накладной(обычно находится на первой странице):', reply_markup = keyboard)

async def load_id_invoices(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['id_invoices'] = message.text
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	keyboard.add('Отмена')
	await FSMInvoices.next()
	await message.reply('Отправьте фото всех листов накладной одним сообщением:', reply_markup = keyboard)
	await bot.send_message(message.from_user.id,'ОБЯЗАТЕЛЬНО ВЫБЕРИТЕ ПУНКТ <<СЖАТЬ ФОТО>>')

async def load_photo_invoices(message: types.Message, state: FSMContext):
	if len(message.photo) == 0:
		await message.reply('Вы не отправили фото')
		return
	code = 'Саня хуй соси'
	async with state.proxy() as data:
		data['photo_invoices'] = message.photo[-1].file_id
	await sqlite_db.sql_add_invoices(state)
	await message.reply(f'Фото успешно загружено', reply_markup = inf.kb(message.from_user.id))
	await state.finish()


def register_handlers_invoices(dp: Dispatcher):
	dp.register_message_handler(cm_start_load_invoices, Text(equals='Загрузить накладную', ignore_case=True), state=None)
	dp.register_message_handler(load_point, state=FSMInvoices.point)
	dp.register_message_handler(load_provider, state=FSMInvoices.provider_invoices)
	dp.register_message_handler(load_date_invoices, state=FSMInvoices.date_invoices)
	dp.register_message_handler(load_sum_invoices, state=FSMInvoices.sum_invoices)
	dp.register_message_handler(load_id_invoices, state=FSMInvoices.id_invoices)
	dp.register_message_handler(load_photo_invoices, content_types=['photo'], state=FSMInvoices.photo_invoices)