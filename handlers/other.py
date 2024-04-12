from aiogram import types, Dispatcher
from create_bot import dp, bot
from datetime import datetime
from id import token
from handlers import inf


#@dp.message_handler()
async def echo_send(message : types.Message):
	await bot.send_message(message.from_user.id, 'Не знаю такой команды') 
	for mod_id in inf.get_mod_id():
		time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
		await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time}: {message.text}')


def register_handlers_other(dp: Dispatcher):
	dp.register_message_handler(echo_send)
