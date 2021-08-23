# -*- coding: utf-8 -*-

import time
import datetime
import random


action_list = ["干饭", "出勤", "理论", "女装", "水群", "卖弱", "看色图", "吃肠粉", "复读",
               "抽卡", "买瓜", "梆人", "饮茶", "挖马路", "喝红茶"]


def cal_luck(user_id: str):
    values = []
    date_time = datetime.datetime.now()
    random.seed(int(user_id) + int(date_time.strftime("%Y%m%d")))
    msg = "\n今日运气值：{}\n".format(random.randint(233, 2000) % 100)
    for i in range(len(action_list)):
        values.append(random.randint(0, 100))
    for i in range(len(action_list)):
        if values[i] < 30:
            msg += f"忌：{action_list[i]}\n"
        elif 70 < values[i]:
            msg += f"宜：{action_list[i]}\n"
    return msg