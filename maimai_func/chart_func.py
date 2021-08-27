import re
import pymysql
from typing import *
from maimai_func.send_help import *
import random
import os
from tools.database import *

try:
    cursor = Cursor()
    random.seed(114514)
except TimeoutError:
    pass


def cal_ratio(user_in: str):
    if user_in == "help":
        return send_help("calculator")
    try:
        chart, user_data = user_in.split()[0], user_in.split()[1:]
    except IndexError:
        return send_help("calculator")
    regex = r"(绿|黄|红|紫|白)([0-9]+)"
    groups = re.match(regex, str(chart)).groups()
    if groups and groups[0] and groups[1]:
        cursor.execute("SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                       "WHERE Id='{}' AND Difficulty='{}'".format(groups[1], groups[0]))
        res = cursor.fetchone()
        if not res:
            return "谱面选择有误......"
    else:
        return send_help("calculator")
    user_form = []
    # split gr, go and miss
    for d in user_data:
        user_form.append(d.split(','))
    for line in user_form[:len(user_form) - 1]:
        if len(line) != 3:
            return send_help("请检查下音符输入数量～")
    if len(user_form[-1]) != 5:
        return send_help("请检查下音符输入数量～")
        # change to int
    for i in range(len(user_form)):
        for j in range(len(user_form[i])):
            user_form[i][j] = int(user_form[i][j])
    if (res[3] and len(user_form) == 5) or (not res[3] and len(user_form) == 4):
        # fill critical perfect notes
        for i in range(len(user_form) - 1):
            user_form[i].insert(0, res[i] - sum(user_form[i]))
        user_form[-1].insert(0, res[-1] - sum(user_form[-1]))
        # check note amounts valid
        for i in range(len(user_form) - 1):
            if not all(0 <= amount <= res[i] for amount in user_form[i]):
                return "请检查下音符输入数量～"
        if not all(0 <= amount <= res[-1] for amount in user_form[-1]):
            return send_help("请检查下音符输入数量～")
            # show notes judgement form
        msg = f"""Tap: {user_form[0][0]} {user_form[0][1]} {user_form[0][2]} {user_form[0][3]}
Hold: {user_form[1][0]} {user_form[1][1]} {user_form[1][2]} {user_form[1][3]}
Slide: {user_form[2][0]} {user_form[2][1]} {user_form[2][2]} {user_form[2][3]}
"""
        if res[3]:
            msg += f"""Touch: {user_form[3][0]} {user_form[3][1]} {user_form[3][2]} {user_form[3][3]}
"""
        msg += f"""Break: {user_form[-1][0]} {user_form[-1][1]} {user_form[-1][2]} {user_form[-1][3]} {user_form[-1][4]} {user_form[-1][5]}
"""
        base_total, ex_total = 1 * res[0] + 2 * res[1] + 3 * res[2] + 5 * res[-1], res[-1]
        base_total += 1 * res[3] if res[3] else 0
        base_user = 0
        note_score = [1, 2, 3, 1]
        judge_ratio = [1, 0.8, 0.5, 0]
        for i in range(len(user_form) - 1):
            for j in range(4):
                base_user += note_score[i] * user_form[i][j] * judge_ratio[j]
        base_user += 5 * ((user_form[-1][0] + user_form[-1][1] + user_form[-1][2]) * 1
                          + user_form[-1][3] * 0.8 + user_form[-1][4] * 0.5)
        ex_user = 1 * user_form[-1][0] + 0.75 * user_form[-1][1] + 0.5 * user_form[-1][2]
        base_ratio, ex_ratio = float('%.4f' % (base_user / base_total * 100)), \
                               float('%.4f' % (ex_user / ex_total))
        achiv = base_ratio + ex_ratio
        msg += f"""基础：{base_ratio}\n额外：{ex_ratio}\n完成率：{base_ratio + ex_ratio}"""
        if 100 <= achiv < 100.5:
            msg += "\n哇哦，鸟了！"
        elif achiv == 101:
            msg += "\n理论值！瞎了！"
        elif base_ratio == 100:
            msg += "\n是 AP！"
        elif 100.5 <= achiv < 101:
            msg += "\n哇哦，鸟加了！"
        return msg
    else:
        return send_help("calculator")


def select_chart(user_in: str):
    if user_in == "help":
        return send_help("view_chart"), None
    try:
        user_in = user_in.strip()
        id, difficulty = user_in[1:], user_in[0]
    except IndexError:
        return send_help("view_chart"), None
    cursor.execute("SELECT * FROM ChartInfo WHERE Id='{}' AND Difficulty='{}'".format(id, difficulty))
    res, img_path = list(cursor.fetchone()), ""
    if res:
        res[1] = res[1].replace('绿', 'Basic').replace('黄', 'Advanced') \
                        .replace('红', 'Expert').replace('紫', 'Master') \
                        .replace('白', 'Re:Master')
        if res[8]:
            msg = f"""ID: {res[0]}
难度：{res[1]}
等级：{res[2]}
定数：{res[3]}
Tap: {res[5]}
Hold: {res[6]}
Slide: {res[7]}
Touch: {res[8]}
Break: {res[9]}
谱师：{res[4]}"""
        else:
            msg = f"""ID: {res[0]}
难度：{res[1]}
等级：{res[2]}
定数：{res[3]}
Tap: {res[5]}
Hold: {res[6]}
Slide: {res[7]}
Break: {res[9]}
谱师：{res[4]}"""
        if os.path.exists("cover/{}.jpg".format(res[0])):
            img_path = f"file://{os.getcwd()}/cover/{res[0]}.jpg"
        elif os.path.exists("cover/{}.png".format(res[0])):
            img_path = f"file://{os.getcwd()}/cover/{res[0]}.png"
    else:
        msg = "谱面不存在哟！检查下 ID 或者难度～"
    return msg, img_path
