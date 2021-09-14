import re
import os
import random
from interact_func.send_help import *
from tools.database import *


difficulty_alias = {"绿": "Basic", "黄": "Advanced", "红": "Expert", "紫": "Master", "白": "Re:Master"}
random.seed(2508)
cursor = Cursor()


def search_by_inner_level(user_in: str):
    user_in = user_in.strip()
    if user_in == "help":
        return send_help("inner_level_search")
    try:
        if user_in[0].isnumeric():
            difficulty, inner_level = None, float(user_in)
        else:
            difficulty, inner_level = user_in[0], float(user_in[1:])
    except IndexError:
        return send_help("inner_level_search")
    if difficulty:
        try:
            difficulty = difficulty_alias[difficulty]
        except KeyError:
            return "难度输入不对哦"
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       f"(SELECT Id FROM ChartInfo WHERE InnerLevel LIKE {inner_level} AND "
                       f"Difficulty='{difficulty}')")
    else:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       f"(SELECT Id FROM ChartInfo WHERE InnerLevel LIKE {inner_level})")
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
    try:
        if user_in[0].isnumeric():
            difficulty, level = None, user_in
        else:
            difficulty, level = user_in[0], user_in[1:]
    except IndexError:
        return send_help("level_search")
    if difficulty:
        try:
            difficulty = difficulty_alias[difficulty]
        except KeyError:
            return "难度输入不对哦"
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       f"(SELECT Id FROM ChartInfo WHERE Level='{level}' AND "
                       f"Difficulty='{difficulty}')")
    else:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       f"(SELECT Id FROM ChartInfo WHERE Level='{level}')")
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
    inner_level, difficulty, level = '', '%', ''
    try:
        if user_in[0].isnumeric():
            if '.' in user_in:
                difficulty, inner_level = '%', float(user_in)
            else:
                difficulty, level = '%', user_in
        else:
            if '.' in user_in:
                difficulty, inner_level = difficulty_alias[user_in[0]], float(user_in[1:])
            else:
                difficulty, level = difficulty_alias[user_in[0]], user_in[1:]
    except IndexError:
        if user_in == "":
            pass
        else:
            return send_help("random_song")
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
