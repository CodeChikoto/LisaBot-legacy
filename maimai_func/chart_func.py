import re
from interact_func.send_help import *
import random
import os
from tools.database import *
import json

random.seed(2508)
with open("./text/difficulty_alias.json", "r") as file:
    difficulty_alias = json.load(file)
    chart_regex = r"(" + r"|".join(difficulty_alias.keys()) + r")([0-9]+)"
cursor = Cursor()


def cal_ratio(user_in: str):
    global difficulty_alias, chart_regex
    if user_in == "help":
        return send_help("calculator")
    chart, user_data = user_in.split()[0], user_in.split()[1:]
    groups = list(re.match(chart_regex, chart.lower()).groups())
    if groups[0] and groups[1]:
        if groups[0] in difficulty_alias:
            groups[0] = difficulty_alias[groups[0]]
        else:
            return "难度不对呀"
        cursor.execute("SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                       f"WHERE Id='{groups[1]}' AND Difficulty='{groups[0]}'")
        res = cursor.fetchone()
        if not res:
            return "谱面或难度选择有误......"
        user_form = []
        # split gr, go and miss
        for d in user_data:
            user_form.append(d.split(','))
        for line in user_form[:len(user_form) - 1]:
            if len(line) != 3:
                return "请检查下音符输入数量～"
        if len(user_form[-1]) != 5:
            return "请检查下音符输入数量～"
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
                return "请检查下音符输入数量～"
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
            achiv = float('%.4f' % (base_ratio + ex_ratio))
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
        return "检查下输入哦！"
    return send_help("calculator")


def select_chart(user_in: str, difficulty="", id=""):
    global difficulty_alias, chart_regex
    if not difficulty and not id:
        if user_in == "help":
            return send_help("view_chart"), None
        groups = re.match(chart_regex, user_in.lower()).groups()
        id, difficulty = groups[1], difficulty_alias[groups[0]] \
            if groups[0] in difficulty_alias else groups[0]
    cursor.execute(f"SELECT * FROM ChartInfo WHERE Id='{id}' AND Difficulty='{difficulty}'")
    res, img_path = list(cursor.fetchone()), ""
    if not res:
        return "谱面不存在哟！检查下 ID 或者难度～", ""
    if res:
        if res[8]:
            msg = f"""
ID: {res[0]}
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
            msg = f"""
ID: {res[0]}
难度：{res[1]}
等级：{res[2]}
定数：{res[3]}
Tap: {res[5]}
Hold: {res[6]}
Slide: {res[7]}
Break: {res[9]}
谱师：{res[4]}"""
        cursor.execute(f"SELECT Title,Cover,ImageExt FROM SongInfo WHERE Id='{id}'")
        res = cursor.fetchone()
        msg = f"""
标题：{res[0]}""" + msg
        with open("./temp" + res[2], "wb") as cover:
            cover.write(res[1])
        img_path = f"file://{os.getcwd()}/temp" + res[2]
    else:
        msg = "谱面不存在哟！检查下 ID 或者难度～"
    return msg, img_path


def random_chart(user_in: str):
    regex = r"(我要大战)(.+)"
    groups = re.match(regex, user_in).groups()
    if groups[1]:
        keywords = groups[1]
        keywords = keywords.replace("'", "\\'")
        cursor.execute(f"SELECT Id,Difficulty FROM ChartInfo WHERE Charter "
                       f"LIKE '%{keywords}%'")
        res = cursor.fetchall()
        if res:
            chart = random.sample(res, 1)
            return select_chart("", chart[0][1], str(chart[0][0]))
        else:
            return "", ""
