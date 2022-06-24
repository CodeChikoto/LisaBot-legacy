from maimai_func.song_func import *
from maimai_func.chart_func import *
from maimai_func.user_data_func import *
from tools.image import *
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from tools.shared_var import *
from maimai_func.offline_func import *


garupa_level_search = on_regex("^等级查曲 ([0-9]{1,2})", priority=2, block=True)
garupa_name_search = on_command("查曲", priority=2, block=True)
garupa_song_random = on_regex("^随机?曲 ([0-9]{1,2})?", priority=2, block=True)
garupa_song_viewing = on_regex("ba?n?g?id ([0-9]+)", priority=2, block=True)
card_search = on_regex("查卡 (.+)", priority=2, block=True)
card_viewing = on_regex("看卡 (.+)", priority=2, block=True)


