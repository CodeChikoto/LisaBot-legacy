# -*- coding: utf-8 -*-
import multiprocessing
from tools.shared_var import global_var_init, set_global_var
import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot


# You can pass some keyword args config to init function
nonebot.init()
# nonebot.load_builtin_plugins()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter("cqhttp", CQHTTPBot)
driver.config.help_text = {}
nonebot.load_plugins("plugins")


if __name__ == "__main__":
    process_pool = multiprocessing.Pool(4)
    global_var_init()
    set_global_var("process_pool", process_pool)
    nonebot.run(app="bot:app")
