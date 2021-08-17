# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from typing import *


# You can pass some keyword args config to init function
nonebot.init()
# nonebot.load_builtin_plugins()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter("cqhttp", CQHTTPBot)
driver.config.help_text = {}
nonebot.load_plugins("plugins")


if __name__ == "__main__":
    nonebot.run(app="bot:app")