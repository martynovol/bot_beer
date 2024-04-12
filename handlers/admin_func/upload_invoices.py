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

from handlers import inf


class FSMUpInvoices(StatesGroup):
	point = State()
	data1 = State()


async def cm_start_upload_invoices(message: types.Message):
	if True:
		await bot.send_message(message.from_user.id, 'Функция в разработке')
		return
	if message.from_user.id not in inf.get_admin_id():
		await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
		return
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	available_points = inf.get_name_shops()
	for name in available_points:
		keyboard.add(name)
	keyboard.add('Отмена')
	await message.reply('Выберите точку:', reply_markup = keyboard)
	await FSMUpInvoices.point.set()


async def load_point_upload_invoices(message: types.Message, state: FSMContext):
	available_points = inf.get_name_shops()
	if message.text not in available_points:
		await bot.send_message(message.from_user.id, 'Выберите точку из предложенных')
		return
	async with state.proxy() as data:
		data['point'] = message.text
	keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
	time = str(datetime.now().strftime('%m.%Y'))
	keyboard.add(time)
	keyboard.add('Отмена')
	await FSMUpInvoices.next()
	await message.reply('Выберите месяц, за который нужно выгрузить накладные:', reply_markup = keyboard)


async def load_data_upload_invoices(message: types.Message, state: FSMContext):
	bit = message.text.split('.')
	if len(bit) != 2 or (len(bit[0]) != 1 and len(bit[0]) != 2) or len(bit[1]) != 4 or not bit[0].isdigit() or not bit[1].isdigit():
		await message.reply(f'Вы ввели некорректное число, попробуйте снова, формат "ММ.ГГГГ"')
		return
	if len(bit[0]) == 1:
		bit[0] = '0' + bit[0] 
	print(bit[0], bit[1])
	async with state.proxy() as data:
		data['data1'] = message.text
		keyboard = InlineKeyboardMarkup()
		invoices = []
		for ret in sqlite_db.cur.execute('SELECT * FROM invoices WHERE point1 LIKE ? AND month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC', [data['point'], bit[0], bit[1]]):
			if ret[0] not in invoices:
				keyboard.add(InlineKeyboardButton(f'{ret[0]} {ret[4]} {ret[8]}', callback_data=f'dho {ret[0]} {message.from_user.id}'))
				invoices.append(ret[0])
	await bot.send_message(message.from_user.id, f'Накладные за {bit[0]}.{bit[1]}', reply_markup = keyboard)
	await state.finish()


def register_handlers_upload_invoices(dp: Dispatcher):
	dp.register_message_handler(cm_start_upload_invoices, Text(equals='Выгрузить накладные', ignore_case=True), state=None)
	dp.register_message_handler(load_point_upload_invoices, state=FSMUpInvoices.point)
	dp.register_message_handler(load_data_upload_invoices, state=FSMUpInvoices.data1)
