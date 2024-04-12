from aiogram import types, Dispatcher
from create_bot import dp, bot
from keyboards import kb_client, kb_inst
from aiogram.dispatcher.filters import Text
from datetime import datetime
from id import token
from handlers import inf
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton


class FSMAccess(StatesGroup):
    mess = State()


async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, f'Привет! Это бот магазина "Дымка". Использовать бота могут только'
                                                 f' сотрудники. Чтобы воспользоваться ботом, запросите доступ у '
                                                 f'модератора, нажав на кнопку "Запросить доступ" ',
                           reply_markup=kb_client)
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id,
                               f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time}: {message.text}')


async def command_access_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    await bot.send_message(message.from_user.id,
                           f'Отправьте сообщение для модератора, чтобы подтвердить свою личность. '
                           f'Например,'
                           f'свою фамилию.', reply_markup=keyboard)
    await FSMAccess.mess.set()


async def load_message_to_access(message: types.Message, state: FSMContext):
    for mod_id in inf.get_admin_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id,
                               f'[{time}]\nПользователь с id: [{message.from_user.id}] запросил доступ к боту.\n'
                               f'Сообщение: {message.text}')
    await message.reply(f'Запрос доступа успешно отправлен, ожидайте проверки модератором', reply_markup=kb_client)
    await state.finish()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start', 'help'])
    dp.register_message_handler(command_access_start, Text(equals='Запросить доступ', ignore_case=True), state=None)
    dp.register_message_handler(load_message_to_access, state=FSMAccess.mess)
