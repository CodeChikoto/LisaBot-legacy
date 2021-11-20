import re
from interact_func.send_help import *
import random
import os
from tools.database import *
from tools.image import *
import json

random.seed(2508)
with open("./text/difficulty_alias.json", "r") as file:
    difficulty_alias = json.load(file)
    chart_regex = r"(" + r"|".join(difficulty_alias.keys()) + r")([0-9]+)"
cursor = Cursor()


def check_combo(user_chart: list[list[int]]):
    state = None
    if all(miss[-1] == 0 for miss in user_chart):
        if all(good[-2] == 0 for good in user_chart):
            if all(great[-3] == 0 for great in user_chart):
                state = "AP+" if user_chart[-1][1] == 0 else "AP"
            else:
                state = "FC+"
        else:
            state = "FC"
    else:
        state = None
    if state == "AP+":
        return "やりましたおめでとうございます\n"
    elif state == "AP":
        return "AP だよ！目に害があった！\n"
    elif state == "FC+" or state == "FC":
        return f"{state} 哇哦～\n"
    else:
        return ""


def cal_achiv_range(user_in: str):
    regex = f"完成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+),([0-9]+)"
    try:
        groups = re.match(regex, user_in).groups()
        difficulty = difficulty_alias[groups[0]] if groups[0] in difficulty_alias else groups[0]
        id = groups[1]
        cursor.execute(f"SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                       f"WHERE Difficulty='{difficulty}' AND Id={id}")
        chart_data = cursor.fetchone()
        if chart_data:
            total_basic = 1 * chart_data[0] + 2 * chart_data[1] + 3 * chart_data[2] + 5 * chart_data[4]
            total_basic += 1 * chart_data[3] if chart_data[3] else 0
            total_ex = chart_data[4]
            user_chart = [[int(groups[2]), int(groups[3]), int(groups[4])],
                          [int(groups[5]), int(groups[6]), int(groups[7])],
                          [int(groups[8]), int(groups[9]), int(groups[10])],
                          [int(groups[11]), int(groups[12]), int(groups[13])],
                          [int(groups[14]), int(groups[15]), int(groups[16]), int(groups[17])]]
            user_basic = 0
            # check
            for i, amount in enumerate(chart_data):
                if not amount:
                    continue
                if not 0 <= sum(user_chart[i]) <= amount:
                    return "输入数量不对哦！"
                user_chart[i].insert(0, amount - sum(user_chart[i]))
            for i, full in enumerate([1, 2, 3, 1]):
                for j, ratio in enumerate([1, 0.8, 0.5]):
                    user_basic += user_chart[i][j] * full * ratio
            max_user_basic = user_basic + 5 * (user_chart[-1][0] + user_chart[-1][1]) + \
                             4 * user_chart[-1][2] + 2 * user_chart[-1][3]
            min_user_basic = user_basic + 5 * (user_chart[-1][0] + user_chart[-1][1]) + \
                             2.5 * user_chart[-1][2] + 2 * user_chart[-1][3]
            max_user_ex = user_chart[-1][0] + 0.75 * user_chart[-1][1] + \
                          0.4 * user_chart[-1][2] + 0.3 * user_chart[-1][3]
            min_user_ex = user_chart[-1][0] + 0.5 * user_chart[-1][1] + \
                          0.4 * user_chart[-1][2] + 0.3 * user_chart[-1][3]
            max_achiv = max_user_basic / total_basic * 100 + max_user_ex / total_ex
            min_achiv = min_user_basic / total_basic * 100 + min_user_ex / total_ex
            return f"{round(max_achiv, 4)}% ~ {round(min_achiv, 4)}%\n" \
                   f"结果可能存在略微偏差\n" + check_combo(user_chart)
        else:
            return "没有这个谱面捏"
    except AttributeError:
        return send_help("calculator")


def cal_break_dist(user_in: str):
    regex = f"绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+.[0-9]+)"
    try:
        groups = re.match(regex, user_in).groups()
        difficulty = difficulty_alias[groups[0]] if groups[0] in difficulty_alias else groups[0]
        id = groups[1]
        ans = []
        cursor.execute(f"SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                       f"WHERE Difficulty='{difficulty}' AND Id={id}")
        chart_data = cursor.fetchone()
        if chart_data:
            total_basic = 1 * chart_data[0] + 2 * chart_data[1] + 3 * chart_data[2] + 5 * chart_data[4]
            total_basic += 1 * chart_data[3] if chart_data[3] else 0
            total_ex = chart_data[4]
            user_chart = [[int(groups[2]), int(groups[3]), int(groups[4])],
                          [int(groups[5]), int(groups[6]), int(groups[7])],
                          [int(groups[8]), int(groups[9]), int(groups[10])],
                          [int(groups[11]), int(groups[12]), int(groups[13])],
                          [int(groups[14]), int(groups[15]), int(groups[16]), int(groups[17])]]
            user_basic = 0
            # check
            for i, amount in enumerate(chart_data):
                if not amount:
                    continue
                if not 0 <= sum(user_chart[i]) <= amount:
                    return "输入数量不对哦！"
                user_chart[i].insert(0, amount - sum(user_chart[i]))
            for i, full in enumerate([1, 2, 3, 1]):
                for j, ratio in enumerate([1, 0.8, 0.5]):
                    user_basic += user_chart[i][j] * full * ratio
            # break perfect, ex 0.75/0.5
            for i in range(user_chart[-1][1] + 1):
                # break great, basic 4/3/2.5
                # j - 4, k - 3, -j-k - 2.5
                for j in range(user_chart[-1][2] + 1):
                    for k in range(user_chart[-1][2] - j + 1):
                        user_basic_trial = user_basic + 5 * (user_chart[-1][0] + user_chart[-1][1]) + 4 * j + 3 * k + \
                                      2.5 * (user_chart[-1][2] - j - k) + 2 * user_chart[-1][3]
                        user_ex = user_chart[-1][0] + 0.75 * i + 0.5 * (user_chart[-1][1] - i) + \
                                  0.4 * user_chart[-1][2] + 0.3 * user_chart[-1][3]
                        if re.match(groups[18], str(user_basic_trial / total_basic * 100 + user_ex / total_ex)):
                            # [p 0.75, p 0.5, gr 4, gr 3, gr 2.5]
                            ans.append([i, user_chart[-1][1] - i, j, k, user_chart[-1][2] - j - k])
        else:
            return "谱面不存在哟～", None
        if not ans:
            return "可能性がない......", None
        msg = f"Break Perfect 分为0.75/0.5额外分，并且都有5基础分。\n" \
              f"Break Great 分为4/3/2.5基础分，并且都有0.4额外分。"
        for case in ans:
            msg += f"\nP0.75:{case[0]}  P0.5:{case[1]}  Gr4:{case[2]}  Gr3:{case[3]}  Gr2.5:{case[4]}"
        return check_combo(user_chart), text_to_image(msg)
    except AttributeError:
        return send_help("calculator"), None


def select_chart(user_in: str):
    global difficulty_alias, chart_regex
    if user_in == "help":
        return send_help("view_chart"), None
    args = user_in.split()
    groups = re.match(chart_regex, args[0].lower()).groups()
    id, difficulty, version = groups[1], difficulty_alias[groups[0]] \
        if groups[0] in difficulty_alias else groups[0], args[1] if len(args) == 2 else "舞萌DX 2021"
    cursor.execute(f"SELECT SI.Title,SI.Cover,SI.ImageExt,CI.*,CD.Level,CD.InnerLevel,CD.Version FROM ChartInfo CI "
                   f"JOIN ChartDifficulty CD ON CI.Id=CD.Id AND CI.Difficulty=CD.Difficulty "
                   f"JOIN SongInfo SI ON CI.Id=SI.Id "
                   f"WHERE CI.Id={id} AND CI.Difficulty='{difficulty}' AND CD.Version LIKE '%{version}%'")
    res, img_path = cursor.fetchone(), ""
    if not res:
        return "谱面不存在哟！检查下 ID 或者难度～", ""
    if res:
        msg = f"""
标题：{res[0]}
ID: {res[3]}
难度：{res[4]}
等级：{res[11]}
定数：{res[12]}
Tap: {res[6]}
Hold: {res[7]}
Slide: {res[8]}
"""
        if res[9]:
            msg += f"""Touch: {res[9]}
"""
        msg += f"""Break: {res[10]}
谱师：{res[5]}
定级版本：{res[13]}"""
        with open("./temp" + res[2], "wb") as cover:
            cover.write(res[1])
        img_path = f"file://{os.getcwd()}/temp" + res[2]
    else:
        msg = "谱面不存在哟！检查下 ID 或者难度～"
    return msg, img_path


def random_chart(user_in: str):
    regex = r"我要大战(.+)"
    groups = re.match(regex, user_in).groups()
    if groups[0]:
        keywords = groups[0].replace("'", "\\'")
        cursor.execute(f"SELECT CI.Id,CD.Difficulty FROM ChartInfo CI JOIN ChartDifficulty CD "
                       f"ON CI.Id=CD.Id AND CI.Difficulty=CD.Difficulty "
                       f"WHERE CI.Charter LIKE '%{keywords}%'")
        res = cursor.fetchall()
        if res:
            [[id, difficulty]] = random.sample(res, 1)
            return select_chart(difficulty + str(id))
        else:
            return "", ""
