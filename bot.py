# -*- coding: utf-8 -*-


import os
import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from sched import scheduler
import time
from _thread import start_new_thread


def clear_cache():
    for file in os.listdir("./cache"):
        os.remove(f"./cache/{file}")
    cache_cleaner.enter(86400, 0, clear_cache, ())


# You can pass some keyword args config to init function
nonebot.init()
# nonebot.load_builtin_plugins()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter("cqhttp", CQHTTPBot)
driver.config.help_text = {}
nonebot.load_plugins("plugins")
cache_cleaner = scheduler(time.time, time.sleep)


if __name__ == "__main__":
    cache_cleaner.enter(86400, 0, clear_cache, ())
    start_new_thread(cache_cleaner.run, ())
    nonebot.run(app="bot:app")
