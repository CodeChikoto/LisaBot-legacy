import re
import os
import random
from interact_func.send_help import *
from tools.database import *
import json

with open("./text/difficulty_alias.json", "r") as file:
    difficulty_alias = json.load(file)
    chart_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")(.*)"
random.seed(2508)
cursor = Cursor()


def search_by_inner_level(user_in: str):
    user_in = user_in.strip()
    if user_in == "help":
        return send_help("inner_level_search")
    groups = re.match(chart_regex, user_in.lower()).groups()
    difficulty, inner_level = groups[0], float(groups[1])
    if difficulty in difficulty_alias:
        difficulty = difficulty_alias[difficulty]
    else:
        return "输入有误呢～"
    cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                   f"(SELECT Id FROM ChartInfo WHERE InnerLevel LIKE {inner_level} AND "
                   f"Difficulty LIKE '{difficulty}')")
    res = cursor.fetchall()
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = random.sample(res, 30)
    else:
        msg = "搜索结果："
    for song in res:
        msg += f"\n{song[0]}  {song[1]}"
    return msg


def search_by_artist(keyword: str):
    keyword = keyword.strip().replace("'", "\\'")
    cursor.execute(f"SELECT Id,Title FROM SongInfo WHERE Artist LIKE '%{keyword}%'")
    res = cursor.fetchall()
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = random.sample(res, 30)
    else:
        msg = "搜索结果："
    for song in res:
        msg += f"\n{song[0]}  {song[1]}"
    return msg


def search_by_level(user_in: str):
    user_in = user_in.strip()
    if user_in == "help":
        return send_help("level_search")
    groups = re.match(chart_regex, user_in.lower()).groups()
    difficulty, level = groups[0], groups[1]
    if difficulty in difficulty_alias:
        difficulty = difficulty_alias[difficulty]
    else:
        return "输入有误呢～"
    cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                   f"(SELECT Id FROM ChartInfo WHERE Level='{level}' AND "
                   f"Difficulty LIKE '{difficulty}')")
    res = cursor.fetchall()
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = random.sample(res, 30)
    else:
        msg = "搜索结果："
    for song in res:
        msg += f"\n{song[0]}  {song[1]}"
    return msg


def search_by_name(keyword: str):
    if "是什么歌" in keyword:
        regex = "(.+)是什么歌"
        keyword = re.match(regex, keyword).groups()[0]
    keyword = keyword.strip().replace("'", "\\'")
    cursor.execute(f"SELECT Id,Title FROM SongInfo WHERE Title LIKE '%{keyword}%'")
    res = []
    for res_part in cursor.fetchall():
        if res_part not in res:
            res.append(res_part)
    cursor.execute(f"SELECT Id,Title FROM SongInfo WHERE Title IN "
                   f"(SELECT Title FROM SongAlias WHERE Alias='{keyword}')")
    for res_part in cursor.fetchall():
        if res_part not in res:
            res.append(res_part)
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = random.sample(res, 30)
    else:
        msg = "搜索结果："
    for song in res:
        msg += f"\n{song[0]}  {song[1]}"
    return msg


def random_song(user_in: str):
    if user_in == "help":
        return send_help("random_song"), None
    user_in = user_in.strip()
    inner_level, difficulty, level = '', '', ''
    try:
        groups = re.match(chart_regex, user_in.lower()).groups()
        difficulty = groups[0] if groups[0] else '%'
        if difficulty in difficulty_alias:
            difficulty = difficulty_alias[difficulty]
        if '.' in groups[1]:
            inner_level = groups[1]
        else:
            level = groups[1]
    except Exception:
        if user_in:
            return send_help("random_song")
        else:
            pass
    try:
        if inner_level:
            amount = cursor.execute("SELECT Id FROM ChartInfo WHERE InnerLevel LIKE {} AND "
                                    "Difficulty LIKE '{}'".format(inner_level, difficulty))
        elif level:
            amount = cursor.execute("SELECT Id FROM ChartInfo WHERE Level='{}' AND "
                                    "Difficulty LIKE '{}'".format(level, difficulty))
        else:
            amount = cursor.execute("SELECT Id FROM SongInfo")
        rand_int = random.randint(0, amount - 1)
        id = cursor.fetchall()[rand_int][0]
    except ValueError:
        return "随机条件不对哦～", None
    return select_song(id)


def select_song(id: str):
    id = str(id).strip()
    cursor.execute(f"SELECT * FROM SongInfo WHERE Id='{id}'")
    try:
        res = cursor.fetchone()
        msg = f"""
ID: {res[0]}
标题：{res[1]}
艺术家：{res[2]}
BPM: {res[3]}
谱面类型：{res[4]}
分类：{res[5]}
收录版本：{res[6]}
等级："""
        # res[13]: .jpg or .png
        with open("./temp" + res[8], "wb") as cover:
            cover.write(res[7])
        cover.close()
        if res[7]:
            img_path = f"file://{os.getcwd()}/temp" + res[8]
        else:
            img_path = ""
        cursor.execute(f"SELECT Level,InnerLevel FROM ChartInfo WHERE Id='{id}' "
                       "ORDER BY FIELD(Difficulty,'Basic','Advanced',"
                       "'Expert','Master','Re:Master')")
        res = cursor.fetchall()
        level, inner_level = [data[0] for data in res], [data[1] for data in res]
        for i in range(len(inner_level)):
            inner_level[i] = str(inner_level[i])
        msg += ",".join(level)
        msg += '\n定数：'
        msg += ",".join(inner_level)
    except IndexError:
        msg, img_path = "歌曲不存在......", ""
    return msg, img_path
