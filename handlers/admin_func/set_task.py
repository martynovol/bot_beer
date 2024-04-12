import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db


from datetime import datetime
from datetime import date, timedelta

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
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(
        m[2]) == 4
                and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
                and int(m[0]) < 32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


class FSMTask(StatesGroup):
    id = State()
    person = State()
    comments = State()
    time = State()


async def cm_start_set_task(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    users = inf.get_users()
    available_names = []
    for user in users:
        available_names.append(user[1])
    for name in available_names:
        keyboard.add(name)
    keyboard.add('Отмена')
    await message.reply('Выберите сотрудника:', reply_markup=keyboard)
    await FSMTask.person.set()


async def load_person_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['person'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    await FSMTask.next()
    await message.reply('Опишите задачу:', reply_markup=keyboard)


async def load_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comments'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    time = str((datetime.now() + timedelta(hours=1)).strftime('%H:%M'))
    keyboard.add(time)
    keyboard.add('Отмена')
    await FSMTask.next()
    await message.reply('Напишите к какому времени нужно сдать отчёт о выполнении (ЧЧ:ММ):', reply_markup=keyboard)


async def load_date_fine(message: types.Message, state: FSMContext):
    time = message.text.split(':')
    if len(time) != 2 or len(time[0]) != 2 or len(time[1]) != 2 or \
            not (0 < int(time[0]) < 24) or not (0 < int(time[1]) < 60) or \
            datetime.strptime(message.text, "%H:%M") < datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M"):
        await bot.send_message(message.from_user.id, f'Неверный формат времени (ЧЧ:ММ):')
        return
    time = time[0] + ":" + time[1]
    async with state.proxy() as data:
        data['time'], data['accept'], person_id = time, "False", inf.get_user_id(data['person'])
        data['_id'] = message.from_user.id
        users = inf.get_users_id()
        if int(inf.get_user_id(data['person'])) in users:
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton(f'Предоставить отчёт', callback_data=f'task_rep {data["id"]}'))
            await bot.send_message(int(inf.get_user_id(data['person'])),
                                   f'❗️Вам назначена задача на сегодня. Необходимо'
                                   f' её выполнить до назначенного времени и предоставить отчёт о выполнений.\n'
                                   f'Задача: {data["comments"]}\nДедлайн: {data["time"]}', reply_markup=keyboard)
    await sqlite_db.sql_add_task(state)
    await state.finish()
    await bot.send_message(message.from_user.id, 'Задача назначена. Сотрудник уведомлен.',
                           reply_markup=inf.kb(message.from_user.id))
    await remind_task(message.from_user.id, time, person_id)


async def remind_task(id1, close_time, person_id):
    try:
        time_now = str(datetime.now().strftime('%H:%M'))
        now_time = datetime.strptime(time_now, "%H:%M")
        close_time = datetime.strptime(close_time, "%H:%M")  # - timedelta(hours=0, minutes=15)
        try:
            s = now_time > close_time
        except Exception:
            return
        time_dif = str(close_time - now_time).split(':')
        hours, minutes = float(time_dif[0]) * 60 * 60, float(time_dif[1]) * 60
        total_time = hours + minutes
        await asyncio.sleep(total_time)
        check = 0
        for ret in sqlite_db.cur.execute('SELECT id FROM tasks WHERE person LIKE ? '
                                         'AND time LIKE ?', [inf.get_name(person_id),
                                                             close_time.strftime('%H:%M')]):
            check = ret[0]
        if check != 0:
            await bot.send_message(id1,
                                   f'❗️Сотрудник {inf.get_name(person_id)}'
                                   f' не предоставил отчёт о выполнении задачи в срок')
    except Exception:
        return


async def take_all_task(message: types.Message):
    keyboard = InlineKeyboardMarkup()

    async def get_tasks(sql, value):
        task = False
        for ret in sqlite_db.cur.execute(sql, value).fetchall():
            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('Отменить', callback_data=f"del_task {ret[0]}"))
            for jet in sqlite_db.cur.execute("SELECT task_id FROM task_report WHERE task_id LIKE ?", [ret[0]]).fetchall():
                task = jet[0]
            if task:
                keyboard.insert(InlineKeyboardButton('Отчёты', callback_data=f"last_task {task}"))
            await bot.send_message(message.from_user.id, f'Продавец: {ret[1]} | Дедлайн: {ret[3]}\nЗадача: {ret[2]}',
                                   reply_markup=keyboard)

    if message.from_user.id in inf.get_mod_id():
        await get_tasks("SELECT id, person, comments, time, _id FROM tasks WHERE id <> ?", [""])
    elif message.from_user.id in inf.get_admin_id():
        await get_tasks("SELECT id, person, comments, time, _id FROM tasks WHERE _id LIKE ?", [message.from_user.id])


async def get_last_tasks(callback_query: types.CallbackQuery):
    task_id = callback_query.data.split()[1]
    comment_admin = 0
    for jet in sqlite_db.cur.execute('SELECT photos, comments, comment_admin FROM task_report WHERE task_id LIKE ?',
                                     [task_id]).fetchall():
        await bot.send_message(callback_query.from_user.id, "Отправленные отчёты:")
        media = types.MediaGroup()
        for i, photo in enumerate(jet[0].split()):
            if i == len(jet[0].split()) - 1:
                media.attach_photo(photo, f'Комментарии отчёта: {jet[1]}')
            else:
                media.attach_photo(photo)
        await bot.send_media_group(callback_query.from_user.id, media)
    if comment_admin != 0:
        await bot.send_message(callback_query.from_user.id, f'Комментарии к прошлому отчёту от проверяющего:'
                                                            f' {comment_admin}')
    else:
        keyboards = InlineKeyboardMarkup().add(
                InlineKeyboardButton(f'Принять', callback_data=f"accept_task {task_id}")).insert(
                InlineKeyboardButton(f'Отказать', callback_data=f'dis_task {task_id}'))
        await bot.send_message(callback_query.from_user.id,
                               f'Отчёт на рассмотрении', reply_markup=keyboards)


async def delete_task(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    task_id = callback_query.data.split()[1]
    sqlite_db.cur.execute('DELETE FROM tasks WHERE id LIKE ?', [task_id])
    sqlite_db.cur.execute('DELETE FROM task_report WHERE task_id LIKE ?', [task_id])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, f'Задача отменена')


def register_handlers_task(dp: Dispatcher):
    dp.register_message_handler(cm_start_set_task,
                                Text(equals=f'📔Назначить задачу', ignore_case=True),
                                state=None)
    dp.register_message_handler(take_all_task, Text(equals=f'📔Список задач', ignore_case=True),state=None)
    dp.register_callback_query_handler(get_last_tasks, lambda x: x.data and x.data.startswith('last_task '))
    dp.register_callback_query_handler(delete_task, lambda x: x.data and x.data.startswith('del_task '))
    dp.register_message_handler(load_person_task, state=FSMTask.person)
    dp.register_message_handler(load_task, state=FSMTask.comments)
    dp.register_message_handler(load_date_fine, state=FSMTask.time)
