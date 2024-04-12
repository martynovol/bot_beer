from aiogram.utils import executor
from create_bot import dp
from database import sqlite_db
from handlers import client, admin, other, admin_func, cass_func, mod_func, moysklad
import keyboards


async def on_startup(_):
    print('Bot online')


sqlite_db.sql_start()
cass_func.report_close.register_handlers_close_reports(dp)
admin_func.storage_reports.register_handlers_open_report_storager(dp)
cass_func.report_open.register_handlers_open_report(dp)
#cass_func.my_tasks.register_handlers_get_tasks(dp)
admin_func.per_month.register_handlers_month_report(dp)
admin_func.report_range.register_handlers_range_reports(dp)
admin_func.per_day.register_handlers_day_report(dp)
mod_func.action_with_user.register_handlers_moderator(dp)
mod_func.send_message.register_handlers_send_mes(dp)
admin_func.incassation.register_handlers_incassation(dp)
mod_func.set_salary.register_handlers_salary(dp)
mod_func.points.register_handlers_points(dp)
mod_func.plans_of_sales.register_handlers_plans(dp)
mod_func.plans_of_product.register_handlers_plans_products(dp)
mod_func.revision.register_handlers_revision(dp)
admin_func.zarplata.register_handlers_zarplata(dp)
admin_func.set_fine.register_handlers_fine(dp)
#admin_func.upload_invoices.register_handlers_upload_invoices(dp)
admin_func.payments.register_handlers_payments(dp)
admin_func.debts.register_handlers_debts(dp)
admin_func.problems.register_handlers_get_problems(dp)
#admin_func.set_task.register_handlers_task(dp)
admin_func.premies.register_handlers_premies(dp)
cass_func.defects.register_handlers_loss(dp)
cass_func.take_my_salary.register_handlers_take_my_salary(dp)
cass_func.zamena.register_handlers_zamena(dp)
cass_func.load_invoices.register_handlers_invoices(dp)
#cass_func.instructions.register_handlers_instructions(dp)
cass_func.load_expenses.register_handlers_expenses(dp)
cass_func.local_revision.register_handlers_local_report(dp)
admin_func.upload_sheets.register_handlers_table(dp)


client.register_handlers_client(dp)
moysklad.register_moy_sklad(dp)
keyboards.mod_kb.register_handlers_mod_kb(dp)
keyboards.admin_kb.register_handlers_admin_kb(dp)
admin.register_handlers_admin(dp)
other.register_handlers_other(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
