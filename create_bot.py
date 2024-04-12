from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from id import token

import os
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage=MemoryStorage()

token1 = token.TokenBot


bot = Bot(token=token1)
dp = Dispatcher(bot, storage=storage)

