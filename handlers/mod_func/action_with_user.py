from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher, contrib
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from create_bot import dp, bot
from database import sqlite_db
from aiogram.contrib.fsm_storage.memory import MemoryStorage as mems
from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb
from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from handlers.cass_func import report_open

import emoji

get_data = []


class FSMNew_user(StatesGroup):
    id1 = State()
    name = State()
    privileges = State()


class FSMDel_user(StatesGroup):
    id1 = State()


class FSMGet_user(StatesGroup):
    id1 = State()


class FSMGet_user_button(StatesGroup):
    id1 = State()

class FSMSet_user_state(StatesGroup):
    id1 = State()

class FSMGet_user_state(StatesGroup):
    id1 = State()


class FSMAdd_points(StatesGroup):
    name = State()
    id1 = State()
    state_continue = State()


# Список точек
def global_dictionary(data, method):
    if method == "add":
        get_data.append(data)
    elif method == "check":
        return get_data
    elif method == "clear":
        get_data.clear()


async def add_new_user(message: types.Message):
    if message.from_user.id not in inf.get_admin_id() and message.from_user.id != 761694862:
        await bot.send_message(message.from_user.id, 'Вам не доступна эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    await bot.send_message(message.from_user.id, 'Id: ', reply_markup=keyboard)
    await bot.send_message(761694862, f'{message.from_user.id} начал добавлять пользователя')
    await FSMNew_user.id1.set()


async def set_new_user_id(message: types.Message, state: FSMContext):
    users_id = []
    for ret in sqlite_db.cur.execute('SELECT id FROM users'):
        users_id.append(ret[0])
    if message.text in users_id:
        await message.reply(f'Пользователь с таким id уже существует',
                            reply_markup=inf.kb(message.from_user.id))
        await state.finish()
        return
    async with state.proxy() as data:
        data['id1'] = int(message.text)
    await FSMNew_user.next()
    await message.reply('Введите имя пользователя:')


async def set_new_user_name(message: types.Message, state: FSMContext):
    users = []
    for ret in sqlite_db.cur.execute('SELECT person FROM users'):
        users.append(ret[0])
    if message.text in users:
        await message.reply(f'Пользователь с таким именем уже существует', reply_markup=inf.kb(message.from_user.id))
        await state.finish()
        return
    async with state.proxy() as data:
        data['name'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Модератор').insert('Администратор').row('Кассир')
    await FSMNew_user.next()
    await bot.send_message(message.from_user.id, 'Выберите привилегию пользователя', reply_markup=keyboard)


async def set_new_user_privileges(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['privileges'] = message.text
        await bot.send_message(761694862, f'{message.from_user.id} добавил пользователя {tuple(data.values())}')
        id_user = data['id1']
    await sqlite_db.sql_add_user(state)
    try:
        await bot.send_message(id_user,
                               f'Добро пожаловать в бот "Дымка". Если клавиатура не обновилась впишите команду "/admin".',
                               reply_markup=inf.kb(id_user))
        await state.finish()
    except Exception:
        await state.finish()

    await bot.send_message(message.from_user.id, 'Пользователь успешно добавлен', reply_markup=mod_kb.button_case_mod)


async def list_users(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна эта функция')
        return
    await bot.send_message(message.from_user.id, 'Выгружаю список всех пользователей:')
    for user in inf.get_users():
        result = ''
        if user[3] != '0' and not (user[3] is None):
            for point in user[3].split(' '):
                result += inf.pt_name(point) + ','
        else:
            result = 'Отсутствуют'
        await bot.send_message(message.from_user.id,
                               f'Id: {user[0]}\nИмя: {user[1]}\nПривилегия: {user[2]}\nТочки:{result}',
                               reply_markup=InlineKeyboardMarkup()
                               .add(InlineKeyboardButton(f'Точки {user[1]}', callback_data=f'add_p {user[0]}'))
                               .insert(InlineKeyboardButton(f'Удалить {user[1]}', callback_data=f'rem_p {user[0]}'))#.row(
                                   #InlineKeyboardButton(f'Надбавки {user[1]}', callback_data=f'bonus_user {user[0]}')
                               )
    await bot.send_message(message.from_user.id, 'Список выгружен')


async def delete_user(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    user_id = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM users WHERE id LIKE ?', [user_id])
    sqlite_db.base.commit()
    await callback_query.message.answer(f'Пользователь удалён', reply_markup=inf.kb(callback_query.from_user.id))


async def add_point_start(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    user_id = callback_query.data.split(' ')[1]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for ret in sqlite_db.cur.execute('SELECT points FROM users WHERE id LIKE ?', [user_id]):
        last_point = str(ret[0])
    global_dictionary("", "clear")
    if last_point == '0':
        i = 1
        for ret in inf.get_name_shops():
            if i % 2 == 0:
                keyboard.insert(str(ret))
            else:
                keyboard.row(str(ret))
            i += 1
        global_dictionary([user_id], "add")
    else:
        i = 1
        for ret in sqlite_db.cur.execute('SELECT id, name_point FROM shops').fetchall():
            if ret[0] not in last_point.split(' '):
                if i % 2 == 0:
                    keyboard.insert(str(ret[1]))
                else:
                    keyboard.row(str(ret[1]))
                i += 1
        global_dictionary([user_id, last_point], "add")
    keyboard.row('Убрать все точки')
    keyboard.insert('Отмена')
    await callback_query.message.answer(f'Выберите точку, которую необходимо добавить:', reply_markup=keyboard)
    await FSMAdd_points.id1.set()


async def add_test(message: types.Message, state: FSMContext):
    user_id = global_dictionary("", "check")[0][0]
    current_state = await state.get_state()
    if current_state == "FSMAdd_points:state_continue":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        last_points = '0'
        for ret in sqlite_db.cur.execute('SELECT points FROM users WHERE id LIKE ?', [user_id]):
            last_points = ret[0]
        i = 1
        for ret in sqlite_db.cur.execute('SELECT id, name_point FROM shops').fetchall():
            if ret[0] not in last_points.split(' '):
                if i % 2 == 0:
                    keyboard.insert(str(ret[1]))
                else:
                    keyboard.row(str(ret[1]))
                i += 1
        keyboard.row('Убрать все точки')
        keyboard.insert('Отмена')
        await message.reply(f'Выберите ещё одну точку, которую необходимо добавить:', reply_markup=keyboard)
        await FSMAdd_points.id1.set()
    else:
        await message.reply(f'Использование данной функции невозможно', reply_markup=inf.kb(message.from_user.id))
        await state.finish()


async def finish_add_point(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == "FSMAdd_points:state_continue":
        await bot.send_message(message.from_user.id, f'Точки пользователя успешно обновлены',
                               reply_markup=inf.kb(message.from_user.id))
        await state.finish()
        return
    elif current_state == "FSMProblem:state_continue":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
        await bot.send_message(message.from_user.id, f'Фото успешно загружены. Опишите проблемы:', reply_markup=keyboard)
        await report_open.FSMProblem.next()


async def delete_points(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    user_id = global_dictionary("", "check")[0][0]
    if current_state == "FSMAdd_points:id1":
        sqlite_db.cur.execute('UPDATE users SET points = ? WHERE id LIKE ?', ['0', user_id])
        sqlite_db.base.commit()
        await bot.send_message(message.from_user.id, f'Точки пользователя убраны',
                               reply_markup=inf.kb(message.from_user.id))
        await state.finish()
        return


async def set_id_state(message: types.Message, state: FSMContext):
    user_id = global_dictionary("", "check")[0][0]
    shop_id = str(inf.get_id_point(message.text))
    result = shop_id
    for ret in sqlite_db.cur.execute('SELECT points FROM users WHERE id LIKE ?', [user_id]):
        last_id = str(ret[0])
    if last_id != '0':
        result = last_id + ' ' + shop_id
    sqlite_db.cur.execute('UPDATE users SET points = ? WHERE id LIKE ?', [result, user_id])
    sqlite_db.base.commit()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Далее')
    keyboard.insert('Отмена')
    keyboard.row('Закончить')
    await bot.send_message(message.from_user.id, f'Вы выбрали {message.text}', reply_markup=keyboard)
    await FSMAdd_points.next()


async def set_test_contiune(message: types.Message, state: FSMContext):
    await state.finish()


async def get_user_buttons(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await message.answer(f'Нет доступа к команде')
        return
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    for user in inf.get_users():
        keyboards.add(user[1])
    keyboards.add('Отмена')
    await bot.send_message(message.from_user.id, f'User:', reply_markup=keyboards)
    await FSMGet_user.id1.set()


async def get_user_buttons_id(message: types.Message, state: FSMContext):
    user_id = int(inf.get_user_id(message.text))
    await bot.send_message(message.from_user.id, f'{list(inf.kb(user_id))}',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def update_user_button(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        await message.answer(f'Нет доступа к команде')
        return
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    for user in inf.get_users():
        keyboards.add(user[1])
    keyboards.add('Отмена')
    await bot.send_message(message.from_user.id, f'User:', reply_markup=keyboards)
    await FSMGet_user_button.id1.set()


async def update_user_button_id(message: types.Message, state: FSMContext):
    user_id = int(inf.get_user_id(message.text))
    user_state = dp.current_state(user=user_id, chat=user_id)
    await user_state.set_state()
    await bot.send_message(user_id, f'Ваша клавиатура обновлена',
                           reply_markup=inf.kb(user_id))
    await bot.send_message(message.from_user.id, f'Successful', reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def get_state_user(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    for user in inf.get_users():
        keyboards.add(user[1])
    keyboards.add('Отмена')
    await bot.send_message(message.from_user.id, f'User:', reply_markup=keyboards)
    await FSMGet_user_state.id1.set()


async def get_state_user_id(message: types.Message, state: FSMContext):
    user_id = int(inf.get_user_id(message.text))
    user_state = dp.current_state(user=user_id, chat=user_id)
    await bot.send_message(message.from_user.id, f'User:{str(await user_state.get_state())}\n'
                                                 f'Data:{str(await user_state.get_data())}',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def get_all_user_state(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    users, text = inf.get_users(), 'States:\n'
    for user in users:
        user_id, user_name = int(user[0]), user[1]
        try:
            user_state = dp.current_state(user=user_id, chat=user_id)
            user_state = str(await user_state.get_state())
            if user_state != "None":
                text += f'{user_name}: {user_state}\n'
        except Exception:
            text += ''
    keyboards = InlineKeyboardMarkup().add(InlineKeyboardButton('Update', callback_data="up_state "))
    await bot.send_message(message.from_user.id, text, reply_markup=keyboards)


async def instruction(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    await message.answer(f'/but - get button user\n/upbut - update button user (state = None)\n'
                         f'/gsta - get state users\n/gst - get state, data user\n'
                         f'/updb [com]\n/sql - sql instr\n'
                         f'/gtbc [table] - columns\n/gtb - tables',
                         reply_markup=inf.kb(message.from_user.id))


async def update_database_t(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    try:
        sqlite_db.cur.execute(message.get_args())
        sqlite_db.base.commit()
        await bot.send_message(message.from_user.id, "Up OK!")
    except Exception:
        pass


async def get_columns(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    args = message.get_args()
    if len(args) != 0:
        result = ''
        for ret in sqlite_db.cur.execute(f'PRAGMA table_info({args})'):
            result += f'{ret[0]}: {ret[1]}\n'
        if result != '':
            await bot.send_message(message.from_user.id, result)


async def get_tables(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    result, i = '', 0
    for ret in sqlite_db.cur.execute("""select * from sqlite_master where type = 'table'"""):
        result += f'{i}: {ret[1]}\n'
        i += 1
    if result != '':
        await bot.send_message(message.from_user.id, result)


async def get_sql_command(message: types.Message):
    if message.from_user.id not in inf.get_mod_id():
        return
    await bot.send_message(message.from_user.id, f'1. INSERT INTO table VALUES("")\n'
                                                 f'2. UPDATE table SET arg = ?\n'
                                                 f'3. DELETE FROM table WHERE arg LIKE ?')


async def get_bonus_user(callback_query: types.CallbackQuery):
    uid = callback_query.data.split()[1]
    kb = InlineKeyboardMarkup()
    for ret in sqlite_db.cur.execute('SELECT id, user_id, date1, count, is_per, is_minus FROM prize_user WHERE user_id LIKE ?', [uid]).fetchall():
        kb.add(InlineKeyboardButton('Удалить', callback_data=f"del_bonus {ret[0]}"))
        await bot.send_message(callback_query.from_user.id,
                               f'Надбавка {uid} | Дата {ret[2]}\nИзменение: {ret[5]}{ret[4]}{ret[3]}', reply_markup=kb)


async def del_bonus_user(callback_query: types.CallbackQuery):
    uid = callback_query.data.split()[1]
    sqlite_db.cur.execute('DELETE FROM prize_users WHERE id LIKE ?', uid)
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, 'Удалено')


async def update_user_state(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in inf.get_mod_id():
        return
    users, text = inf.get_users(), 'States:\n'
    for user in users:
        user_id, user_name = int(user[0]), user[1]
        try:
            user_state = dp.current_state(user=user_id, chat=user_id)
            user_state = str(await user_state.get_state())
            if user_state != "None":
                text += f'{user_name}: {user_state}\n'
        except Exception:
            text += ''
    keyboards = InlineKeyboardMarkup().add(InlineKeyboardButton('Update', callback_data="up_state "))
    await callback_query.message.edit_text(text=text)
    await callback_query.message.edit_reply_markup(reply_markup=keyboards)



def register_handlers_moderator(dp: Dispatcher):
    # Написать письмо(только модератор)
    dp.register_message_handler(add_test, Text(equals='Далее', ignore_case=True), state="*")
    dp.register_message_handler(finish_add_point, Text(equals='Закончить', ignore_case=True), state="*")
    dp.register_message_handler(instruction, Text(equals='мод', ignore_case=True), state="*" )
    dp.register_message_handler(get_all_user_state, Text(equals='/gsta', ignore_case=True), state="*")
    # Получение кнопок user
    dp.register_message_handler(get_user_buttons, Text(equals='/but', ignore_case=True), state="*")
    dp.register_message_handler(get_user_buttons_id, state=FSMGet_user.id1)
    # Обновление кнопок user
    dp.register_message_handler(update_user_button, Text(equals='/upbut', ignore_case=True), state="*")
    dp.register_message_handler(update_user_button_id, state=FSMGet_user_button.id1)
    # Получение state user
    dp.register_message_handler(get_state_user, Text(equals='/gst', ignore_case=True), state="*")
    dp.register_message_handler(get_state_user_id, state=FSMGet_user_state.id1)
    dp.register_message_handler(update_database_t, commands='updb', state="*")
    # Получение колонок таблицы
    dp.register_message_handler(get_columns, commands='gtbc', state="*")
    dp.register_message_handler(get_sql_command, commands='sql', state="*")
    # Получение списка табилц
    dp.register_message_handler(get_tables, commands='gtb', state="*")
    dp.register_message_handler(delete_points, Text(equals='Убрать все точки', ignore_case=True), state="*")
    # Добавление нового пользователя в базу(только модератор)
    dp.register_message_handler(add_new_user, Text(equals='Добавить пользователя', ignore_case=True), state=None)
    dp.register_message_handler(set_new_user_id, state=FSMNew_user.id1)
    dp.register_message_handler(set_new_user_name, state=FSMNew_user.name)
    dp.register_message_handler(set_new_user_privileges, state=FSMNew_user.privileges)
    # Удаление пользователя из базы(только модератор)
    dp.register_message_handler(list_users, Text(equals='Список пользователей', ignore_case=True), state=None)
    # dp.register_message_handler(del_id, state=FSMDel_user.id1)
    dp.register_callback_query_handler(add_point_start, lambda x: x.data and x.data.startswith('add_p '))
    dp.register_callback_query_handler(delete_user, lambda x: x.data and x.data.startswith('rem_p '))
    dp.register_callback_query_handler(get_bonus_user, lambda x: x.data and x.data.startswith('bonus_user '))
    dp.register_callback_query_handler(del_bonus_user, lambda x: x.data and x.data.startswith('del_bonus '))
    dp.register_callback_query_handler(update_user_state, lambda x: x.data and x.data.startswith('up_state '))
    dp.register_message_handler(set_id_state, state=FSMAdd_points.id1)
    dp.register_message_handler(set_test_contiune, state=FSMAdd_points.state_continue)
