import sqlite3 as sq
from create_bot import bot
from datetime import datetime
from datetime import date, timedelta
import random
import string
from handlers import inf


def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.sample(letters_and_digits, 25))


def sql_start():
    global base, cur
    base = sq.connect('report.db')
    cur = base.cursor()
    base.execute(
        'CREATE TABLE IF NOT EXISTS menu(person TEXT,point1 TEXT,date1 DATE, day TEXT, month TEXT, year TEXT, '
        'cash TEXT, non_cash TEXT, transfers TEXT, total TEXT, in_box TEXT, in_vault TEXT, expenses TEXT, '
        'comments TEXT, photo1 TEXT, photo2 TEXT, id TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS last_report(person TEXT,point1 TEXT,date1 DATE, day TEXT, month TEXT, year TEXT, '
        'cash TEXT, non_cash TEXT, transfers TEXT, total TEXT, in_box TEXT, in_vault TEXT, expenses TEXT, '
        'comments TEXT , photo1 TEXT, photo2 TEXT, data_load TEXT, id TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS users(id TEXT, person TEXT, privileges TEXT, points TEXT, date1 TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS replace_person(data1 TEXT, time TEXT, person1 TEXT, person TEXT, id TEXT,'
                 'report_open_id TEXT, report_close_id TEXT, point TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS fine(person TEXT, fine TEXT, date1 TEXT, day TEXT, month TEXT, year TEXT, '
        'comments TEXT,id TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS invoices(id TEXT, person TEXT, point1 TEXT, provider_invoices TEXT,date_invoices '
        'TEXT, day TEXT, month TEXT, year TEXT, sum_invoices TEXT, photo_invoices TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS shops(id TEXT, name_point TEXT, work_hours_start TEXT, work_hours_finish TEXT, '
        'difference_time TEXT, id_sklad TEXT, url_api TEXT)')
    #base.execute('CREATE TABLE IF NOT EXISTS temp(id TEXT, temp_value TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS payments(id TEXT, person TEXT, date1 TEXT, month TEXT, year TEXT, '
                 'payment TEXT, date2 TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS reports_open(id TEXT, person TEXT, point1 TEXT, date1 TEXT, in_box TEXT, '
                 'in_vault TEXT, selfie TEXT, problem_photos TEXT, comments TEXT, report_close_id TEXT, now_user TEXT)')
    #base.execute('CREATE TABLE IF NOT EXISTS test(name TEXT, id TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS salary(id TEXT, point_id TEXT, date TEXT, type TEXT, int TEXT, value TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS prize(salary_id TEXT, inter1 TEXT, inter2 TEXT, prize_count TEXT, is_per TEXT, is_step TEXT)')
    base.execute(
        'CREATE TABLE IF NOT EXISTS defects(id TEX, point_id TEXT, point_name TEXT, date TEXT, type TEXT,'
        ' product_id TEXT, product_name TEXT, price TEXT, photo TEXT, comments TEXT, month TEXT, year TEXT, token_id TEXT, user_id TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT, person TEXT, comments TEXT, time TEXT, accept TEXT, _id TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS task_report(photos TEXT, comments TEXT, comment_admin ,task_id TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS prize_user(id TEXT, user_id TEXT, date1 TEXT, day_month TEXT, count TEXT, is_per TEXT, is_minus TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS categories_expenses(id TEXT, point TEXT, name TEXT, value TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS categories_invoices(id TEXT, name TEXT, type TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS invoice_user(id TEXT, comment TEXT, value TEXT, category TEXT, photo TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS premies(id TEXT, person TEXT, date1 TEXT, premie TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS plans_shop(store_id TEXT, group1 TEXT, group_name TEXT, value TEXT, prem TEXT, month TEXT, year TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS premies_plan(person TEXT, premie TEXT, month TEXT, year TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS premies_plan_point(point TEXT, premie TEXT, month TEXT, year TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS revision(id TEXT, point TEXT, value TEXT, date TEXT, month TEXT, year TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS late(id TEXT, id_user TEXT, day TEXT, month TEXT, year TEXT, time_open TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS local_revision(id TEXT, user_id TEXT,point_id TEXT, day TEXT, month TEXT, year TEXT, last_user_id TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS local_revision_position(id TEXT, id_revision TEXT, name_position TEXT, stock TEXT, now_stock TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS incassations(id TEXT, person_id TEXT, point_id TEXT, day TEXT, month TEXT, year TEXT, start_date TEXT, end_date TEXT,count TEXT, comments TEXT, approve TEXT, real_time TEXT)')
    
    base.execute('CREATE TABLE IF NOT EXISTS storager_report(id TEXT, person_id TEXT, now_time TEXT, day TEXT, month TEXT, year TEXT, selfie TEXT, opt TEXT, cash TEXT, non_cash TEXT, transfers TEXT, comments TEXT, close TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS driver_report(id TEXT, person_id TEXT, now_time TEXT, day TEXT, month TEXT, year TEXT, selfie TEXT, comments TEXT, close TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS manager_report(id TEXT, person_id TEXT, now_time TEXT, day TEXT, month TEXT, year TEXT, selfie TEXT, comments TEXT, close TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS operator_report(id TEXT, person_id TEXT, now_time TEXT, day TEXT, month TEXT, year TEXT, selfie TEXT, comments TEXT, close TEXT)')

    if base:
        print('Data base connected OK!')
    base.commit()


async def sql_add_command(state):
    async with state.proxy() as data:
        data1 = tuple(data.values())
        date = data1[2].split('.')
        data2 = (
            data1[0], data1[1], data1[2], date[0], date[1], date[2], data1[3], data1[4], data1[5], data1[6], data1[7],
            data1[8], data1[9], data1[12], data1[10], data1[11], data1[13])
        cur.execute('INSERT INTO menu VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', data2)
        base.commit()


async def sql_add_command_last_report(state):
    async with state.proxy() as data:
        data1 = tuple(data.values())
        date = data1[2].split('.')
        id1 = generate_random_string()
        for ret in cur.execute('SELECT id FROM menu WHERE point1 LIKE ? AND date1 LIKE ?', [data1[1], data1[2]]):
            id1 = ret[0]
        data_load = datetime.now() + timedelta(days=1)
        data2 = (
            data1[0], data1[1], data1[2], date[0], date[1], date[2], data1[3], data1[4], data1[5], data1[6], data1[7],
            data1[8], data1[9], data1[12], data1[10], data1[11], str(data_load), id1)
        cur.execute('DELETE FROM last_report WHERE person LIKE ?', [data2[0]])
        cur.execute('INSERT INTO last_report VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?)', data2)
        base.commit()


async def sql_add_user(state):
    async with state.proxy() as data:
        data_users = tuple(data.values())
        cur.execute('INSERT INTO zamena VALUES (?,?,?,?,?)', data_users)
        base.commit()


async def sql_add_invoices(state):
    async with state.proxy() as data:
        data2 = tuple(data.values())
        r = data2[3].split('.')
        data1 = (data2[5], data2[0], data2[1], data2[2], data2[3], r[0], r[1], r[2], data2[4], data2[6])
        cur.execute('INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?,?)', data1)
        base.commit()


async def sql_add_fine(state):
    async with state.proxy() as data:
        data2 = tuple(data.values())
        r = data2[2].split('.')
        id0 = generate_random_string()
        data1 = (data2[0], data2[1], data2[2], r[0], r[1], r[2], data2[3], id0)
        cur.execute('INSERT INTO fine VALUES (?,?,?,?,?,?,?,?)', data1)
        base.commit()


async def sql_add_temp(user_id, temp_value):
    data = (user_id, temp_value)
    cur.execute('INSERT INTO temp VALUES (?,?)', data)
    base.commit()


async def sql_add_salary(state):
    async with state.proxy() as data:
        data1 = tuple(data.values())
        cur.execute('INSERT INTO salary VALUES (?,?,?,?,?,?)', data1)
        base.commit()


async def sql_add_user(state):
    async with state.proxy() as data:
        user_list = tuple(data.values())
        result = (user_list[0], user_list[1], user_list[2], '0', datetime.now().strftime("%d.%m.%Y"))
        cur.execute('INSERT INTO users VALUES (?,?,?,?,?)', result)
        base.commit()


async def sql_add_payment(data):
    data2 = tuple(data)
    id0 = generate_random_string()
    month, year = data2[1].split('.')
    date_now = str(datetime.now().strftime("%d.%m.%Y"))
    result = (id0, data2[0], data2[1], month, year, str(data2[2]), date_now)
    cur.execute('INSERT INTO payments VALUES (?,?,?,?,?,?,?)', result)
    base.commit()


async def sql_read(message):
    for ret in cur.execute("SELECT * FROM menu").fetchall():
        await bot.send_message(message.from_user.id,
                               f'Кассир {ret[0]}\nТочка {ret[1]}\nДата {ret[2]}\nНаличными {ret[3]}\nБезналичными {ret[4]}\nПереводы {ret[5]}\nЗа день {ret[6]}\nВ кассе {ret[7]}\nВ сейфе {ret[8]}\nРасходы {ret[9]}\ns')


async def sql_delete_command(id1):
    cur.execute('DELETE FROM menu WHERE id LIKE ?', [id1])
    base.commit()


async def sql_add_open_report(state):
    async with state.proxy() as data:
        data2 = tuple(data.values())
        cur.execute('INSERT INTO reports_open VALUES (?,?,?,?,?,?,?,?,?,?,?)', data2)
        base.commit()


async def sql_add_point(state):
    async with state.proxy() as data:
        data2 = list(data.values())
        data2.append("")
        data2.append("")
        cur.execute('INSERT INTO shops VALUES (?,?,?,?,?,?,?)', data2)
        base.commit()


async def sql_add_replace_person(state):
    data2 = tuple(state)
    cur.execute('INSERT INTO replace_person VALUES (?,?,?,?,?,?,?,?)', data2)
    cur.execute('UPDATE reports_open SET now_user = ? WHERE id = ?', [data2[2], data2[5]])
    base.commit()


async def sql_add_percent(state):
    async with state.proxy() as data:
        data2 = tuple(data.values())
        cur.execute('INSERT INTO prize VALUES (?,?,?,?,?,?)', data2)
        base.commit()


async def sql_add_defects(state):
    async with state.proxy() as data:
        month, year = data["date"].split('.')[1], data["date"].split('.')[2]
        result = (data["id"], data["point_id"], data["point_name"], data["date"], data['type'],
                  data["product_id"], data["product_name"], data["price"], data["photo"], data["comments"],
                  month, year, data["token_id"], data['user_id'])
        cur.execute('INSERT INTO defects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', result)
        base.commit()



async def sql_add_task(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?)', tuple(data.values()))
        base.commit()


async def sql_add_task_report(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO task_report VALUES (?,?,?,?)', tuple(data.values()))
        base.commit()


async def sql_add_prize_user(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO prize_user VALUES (?,?,?,?,?,?,?)', tuple(data.values()))
        base.commit()


async def sql_add_category_expenses(state):
    async with state.proxy() as data:
        data_categorie = tuple(data.values())
        cur.execute('INSERT INTO categories_expenses VALUES (?,?,?,?)', data_categorie)
        base.commit()


async def info_admin(uid, mes):
    try:
        if uid not in inf.get_users_id():
            await bot.send_message(761694862, f'{uid}: {mes}')
        else:
            await bot.send_message(761694862, f'{inf.get_name(uid)}: {mes}')
    except Exception:
        pass


async def sql_add_category_invoices(state):
    async with state.proxy() as data:
        data_categorie = tuple(data.values())
        cur.execute('INSERT INTO categories_invoices VALUES (?, ?, ?)', data_categorie)
        base.commit()


async def sql_add_premie(state):
    async with state.proxy() as data:
        data1 = tuple(data.values())
        cur.execute('INSERT INTO premies VALUES (?,?,?,?)', data1)
        base.commit()


async def sql_add_plan(dat, date_):
    month, year = date_.split('.')
    cur.execute("DELETE FROM plans_shop WHERE month LIKE ? AND year LIKE ?", [month, year])
    for store in dat.keys():
        for key, value in dat[store].items():
            cur.execute('INSERT INTO plans_shop VALUES (?,?,?,?,?,?,?)',
                        [inf.get_id_point(store), key[1], key[0], value[0], value[1], month, year])
    base.commit()


async def sql_add_premie_plans(user, premie, month, year):
    cur.execute("DELETE FROM premies_plan WHERE month = ? AND year = ?", [month, year])
    cur.execute("INSERT INTO premies_plan VALUES (?,?,?,?)", [user, premie, month, year])
    base.commit()


async def sql_add_revision(state):
    async with state.proxy() as data:
        result = (generate_random_string(), data['point'], data['value'], data['time'], data['month'], data['year'])
        cur.execute('INSERT INTO revision VALUES (?,?,?,?,?,?)', result)
        base.commit()



async def sql_add_manager_report(id_report, person, day, month, year, selfie, time, close = "0"):
    user_data = (id_report, person, time ,day, month, year, selfie, "" ,close)
    cur.execute('INSERT INTO manager_report VALUES (?,?,?,?,?,?,?,?,?)', user_data)
    base.commit()

    
async def sql_add_local_revision(state, person_id, point_id, now_date):
    id_revision = generate_random_string()
    last_user_data, last_user = datetime.strptime(now_date, "%d.%m.%Y") - timedelta(days=1), ""
    for ret in cur.execute("SELECT person FROM menu WHERE date1 = ? AND point1 = ?", [datetime.strftime(last_user_data, "%d.%m.%Y"), inf.pt_name(point_id)]):
        last_user = inf.get_user_id(ret[0])
    day, month, year = now_date.split('.')
    delete_local_revision(day, month, year, point_id)
    result = (id_revision, person_id, point_id, day, month, year, last_user)
    cur.execute('INSERT INTO local_revision VALUES (?,?,?,?,?,?,?)', result)
    async with state.proxy() as data:
        for name_product, stocks in data.items():
            result = (generate_random_string(), id_revision, name_product, stocks[0], stocks[1])
            cur.execute('INSERT INTO local_revision_position VALUES (?,?,?,?,?)', result)
    base.commit()


def delete_local_revision(day, month, year, point_id):
    id = "-----"
    for ret in cur.execute('SELECT id FROM local_revision WHERE day = ? AND month = ? AND year = ? AND point_id = ?', [day,month,year, point_id]):
        id = ret[0]
    cur.execute("DELETE FROM local_revision WHERE id = ?", [id])
    cur.execute("DELETE FROM local_revision_position WHERE id_revision = ?", [id])
    base.commit()


async def sql_add_incassation(rep_id, person_id, point_id, day, month, year, start_date, end_date,count, comments):
    user_data = (rep_id, person_id, point_id ,day, month, year, start_date, end_date, count, comments, "False", str(datetime.now().strftime("%H:%M")))
    cur.execute('INSERT INTO incassations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', user_data)
    base.commit()


async def sql_add_storager_open_report(id_report, person, day, month, year, selfie, time, close = "0"):
    user_data = (id_report, person,time ,day, month, year, selfie, "0", "0", "0", "0", "0", close)
    cur.execute('INSERT INTO storager_report VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', user_data)
    base.commit()


async def sql_add_driver_open_report(id_report, person, day, month, year, selfie, time, close = "0"):
    user_data = (id_report, person,time ,day, month, year, selfie, "" ,close)
    cur.execute('INSERT INTO driver_report VALUES (?,?,?,?,?,?,?,?,?)', user_data)
    base.commit()


async def sql_add_operator_open_report(id_report, person, day, month, year, selfie, time, close = "0"):
    user_data = (id_report, person,time ,day, month, year, selfie, "" ,close)
    cur.execute('INSERT INTO operator_report VALUES (?,?,?,?,?,?,?,?,?)', user_data)
    base.commit()


async def sql_add_driver_close_report(id_report, comments):
    cur.execute('UPDATE driver_report SET comments = ? WHERE id = ?', [comments, id_report])
    cur.execute('UPDATE driver_report SET close = ? WHERE id = ?', [str(datetime.now().strftime('%H:%M')), id_report])
    base.commit()


async def sql_add_operator_close_report(id_report, comments):
    cur.execute('UPDATE operator_report SET comments = ? WHERE id = ?', [comments, id_report])
    cur.execute('UPDATE operator_report SET close = ? WHERE id = ?', [str(datetime.now().strftime('%H:%M')), id_report])
    base.commit()


async def sql_add_storager_close_report(id_report, cash, non_cash, transfers, comments):
    cur.execute('UPDATE storager_report SET cash = ? WHERE id = ?', [cash, id_report])
    cur.execute('UPDATE storager_report SET non_cash = ? WHERE id = ?', [non_cash, id_report])
    cur.execute('UPDATE storager_report SET transfers = ? WHERE id = ?', [transfers, id_report])
    cur.execute('UPDATE storager_report SET comments = ? WHERE id = ?', [comments, id_report])
    cur.execute('UPDATE storager_report SET close = ? WHERE id = ?', [str(datetime.now().strftime('%H:%M')), id_report])
    base.commit()