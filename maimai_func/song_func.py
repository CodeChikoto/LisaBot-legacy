import re
import pymysql
import os
import random
from maimai_func.send_help import *
from tools.database import *

try:
    cursor = Cursor()
    random.seed(2508)
    print("Database succeeded!")
except TimeoutError:
    exit(-1)


def search_by_base(user_in: str):
    user_in = user_in.strip()
    if user_in == "help":
        return send_help("base_search")
    try:
        if user_in[0].isnumeric():
            difficulty, base = None, user_in
        else:
            difficulty, base = user_in[0], user_in[1:]
    except IndexError:
        return send_help("base_search")
    if difficulty:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       f"(SELECT Id FROM ChartInfo WHERE Base='{base}' AND "
                       f"Difficulty='{difficulty}')")
    else:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       f"(SELECT Id FROM ChartInfo WHERE Base='{base}')")
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
    base, difficulty, level = '', '%', ''
    try:
        if user_in[0].isnumeric():
            if '.' in user_in:
                difficulty, base = '%', user_in
            else:
                difficulty, level = '%', user_in
        else:
            if '.' in user_in:
                difficulty, base = user_in[0], user_in[1:]
            else:
                difficulty, level = user_in[0], user_in[1:]
    except IndexError:
        if user_in == "":
            pass
        else:
            return send_help("random_song")
    try:
        if base:
            amount = cursor.execute("SELECT Id FROM ChartInfo WHERE Base='{}' AND "
                                    "Difficulty LIKE'{}'".format(base, difficulty))
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
        msg = f"""ID: {res[0]}
标题：{res[1]}
艺术家：{res[2]}
BPM: {res[3]}
谱面类型：{res[4]}
分类：{res[5]}
收录版本：{res[6]}
等级: {res[7]}, {res[8]}, {res[9]}, {res[10]}"""
        if res[11]:
            msg += f""", {res[11]}"""
        cursor.execute(f"SELECT Base FROM ChartInfo WHERE Id='{id}' "
                       "ORDER BY FIELD(Difficulty,'绿','黄','红','紫','白')")
        res = cursor.fetchall()
        msg += f"""
定数："""
        base_list = [res[i][0] for i in range(len(res))]
        msg += ", ".join(base_list)
    except IndexError:
        msg = "歌曲不存在......"
    if os.path.exists("cover/{}.jpg".format(id)):
        img_path = f"file://{os.getcwd()}/cover/{id}.jpg"
    elif os.path.exists("cover/{}.png".format(id)):
        img_path = f"file://{os.getcwd()}/cover/{id}.png"
    else:
        img_path = ""
    return msg, img_path
