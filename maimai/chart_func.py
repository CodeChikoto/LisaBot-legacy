import re
import pymysql
from typing import *
from pymysql.converters import escape_string
import random


try:
    connection = pymysql.connect(host="127.0.0.1", user="root", password="Root-User",
                                 db="maimai", port=3306)
    random.seed(114514)
    print("Database succeeded!")
except TimeoutError:
    pass


def cal_ratio(chart, user_data: List[str]):
    cursor = connection.cursor()
    regex = r"(绿|黄|红|紫|白)([0-9]+)"
    groups = re.match(regex, str(chart)).groups()
    if groups[0] and groups[1]:
        cursor.execute("SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                       "WHERE Id='{}' AND Difficulty='{}'".format(groups[1], groups[0]))
        res = cursor.fetchall()
        cursor.close()
        if res:
            res = res[0]
        else:
            return "chart input error"
    else:
        return "chart input error"
    if res:
        user_form = []
        for d in user_data:
            user_form.append(d.split(','))
        for line in user_form[:len(user_form) - 1]:
            if len(line) != 3:
                return "user input error"
        if len(user_form[-1]) != 5:
            return "user input error"
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
                if not any(0 <= amount <= res[i] for amount in user_form[i]):
                    return "user input error"
            if not any(0 <= amount <= res[-1] for amount in user_form[-1]):
                return "user input error"
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
            return "user input error"


def select_chart(id, difficulty):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ChartInfo WHERE Id='{}' AND Difficulty='{}'".format(id, difficulty))
    res = cursor.fetchall()
    if res:
        res = list(res[0])
        res[1].replace('绿', 'Basic').replace('黄', 'Adv') \
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
    else:
        msg = "谱面不存在或输入有误！"
    cursor.close()
    return msg