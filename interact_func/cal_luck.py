# -*- coding: utf-8 -*-

import time
import datetime
import random


action_list = ["干饭", "出勤", "理论", "女装", "水群", "卖弱", "看色图", "吃肠粉", "复读",
               "抽卡", "卖瓜", "梆人", "饮茶", "挖马路", "唱打", "蹦迪", "去超商"]
sp_luckness_114514 = "\n今日运气值：1145141919810\n宜：喝红茶\n宜：雷普\n宜：哼哼啊\n" \
                     "宜：目力打歌\n宜：やりますね"
sp_luckness_39 = "\n今日运气值：3939\n宜：带 fu 出勤\n宜：我草！初音未来！\n" \
                 "宜：扮成初音未来"


def cal_luck(user_id: str):
    values = []
    date_time = datetime.datetime.now()
    random.seed(int(user_id) + int(date_time.strftime("%Y%m%d")))
    luckness = random.randint(233, 2000)
    if luckness in [240, 810, 1145, 1919]:
        msg = sp_luckness_114514
    elif luckness % 100 == 39:
        msg = sp_luckness_39
    else:
        msg = f"\n今日运气值：{luckness % 100}\n"
        for i in range(len(action_list)):
            values.append(random.randint(0, 100))
        for i in range(len(action_list)):
            if values[i] < 30:
                msg += f"忌：{action_list[i]}\n"
            elif 70 < values[i]:
                msg += f"宜：{action_list[i]}\n"
    return msg