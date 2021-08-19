import re
import pymysql
import os
import random
from maimai_func.send_help import *

try:
    connection = pymysql.connect(host="127.0.0.1", user="root", password="Root-User",
                                 db="maimai", port=3306)
    random.seed(114514)
    print("Database succeeded!")
except TimeoutError:
    exit(-1)


def search_by_base(user_in: str):
    if user_in == "help":
        return send_help("base_search")
    try:
        if user_in[0].isnumeric():
            difficulty, base = None, user_in
        else:
            difficulty, base = user_in[0], user_in[1:]
    except IndexError:
        return send_help("base_search")
    cursor = connection.cursor()
    if difficulty:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       "(SELECT Id FROM ChartInfo WHERE Base='{}' AND "
                       "Difficulty='{}')".format(base, difficulty))
    else:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       "(SELECT Id FROM ChartInfo WHERE Base='{}')".format(base))
    res = cursor.fetchall()
    msg = "搜索结果："
    for song in res:
        msg += "\n{}  {}".format(song[0], song[1])
    cursor.close()
    return msg


def search_by_level(user_in: str):
    if user_in == "help":
        return send_help("level_search")
    try:
        if user_in[0].isnumeric():
            difficulty, level = None, user_in
        else:
            difficulty, level = user_in[0], user_in[1:]
    except IndexError:
        return send_help("level_search")
    cursor = connection.cursor()
    if difficulty:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       "(SELECT Id FROM ChartInfo WHERE Level='{}' AND "
                       "Difficulty='{}')".format(level, difficulty))
    else:
        cursor.execute("SELECT Id,Title FROM SongInfo WHERE Id IN "
                       "(SELECT Id FROM ChartInfo WHERE Level='{}')"
                       .format(level))
    res = list(cursor.fetchall())
    if len(res) > 20:
        msg = "结果过多，仅显示20条："
        res = random.sample(res, 20)
    else:
        msg = "搜索结果："
    for song in res:
        msg += "\n{}  {}".format(song[0], song[1])
    cursor.close()
    return msg


def search_by_name(keyword: str):
    if "是什么歌" in keyword:
        regex = "(.+)是什么歌"
        keyword = re.match(regex, keyword).groups()[0].strip()
    cursor = connection.cursor()
    cursor.execute("SELECT Id,Title FROM SongInfo WHERE Title LIKE '%{}%'".format(keyword))
    res = []
    for res_part in cursor.fetchall():
        if res_part not in res:
            res.append(res_part)
    cursor.execute("SELECT Id,Title FROM SongInfo WHERE Title IN "
                   "(SELECT Title FROM SongAlias WHERE Alias='{}')".format(keyword))
    for res_part in cursor.fetchall():
        if res_part not in res:
            res.append(res_part)
    if len(res) > 20:
        msg = "结果过多，仅显示20条："
        res = random.sample(res, 20)
    else:
        msg = "搜索结果："
    for song in res:
        msg += "\n{}  {}".format(song[0], song[1])
    cursor.close()
    return msg


def random_song(user_in: str):
    if user_in == "help":
        return send_help("random_song"), None
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
    cursor = connection.cursor()
    try:
        if base:
            amount = cursor.execute("SELECT Id FROM ChartInfo WHERE Base='{}' AND "
                                    "Difficulty LIKE'{}'".format(base, difficulty))
            for _ in range(random.randint(1, amount) - 1):
                cursor.fetchone()
        elif level:
            amount = cursor.execute("SELECT Id FROM ChartInfo WHERE Level='{}' AND "
                                    "Difficulty LIKE '{}'".format(level, difficulty))
            for _ in range(random.randint(1, amount) - 1):
                cursor.fetchone()
        else:
            amount = cursor.execute("SELECT Id FROM SongInfo")
            for _ in range(random.randint(1, amount) - 1):
                cursor.fetchone()
        id = cursor.fetchone()[0]
    except ValueError:
        cursor.close()
        return "随机条件不对哦～", None
    cursor.close()
    return select_song(id)


def select_song(id: str):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM SongInfo WHERE Id='{}'".format(id))
    try:
        res = cursor.fetchone()
        msg = f"""ID: {res[0]}
标题：{res[1]}
艺术家：{res[2]}
BPM: {res[3]}
谱面类型：{res[4]}
分类：{res[5]}
收录版本：{res[6]}
Level: {res[7]}, {res[8]}, {res[9]}, {res[10]}"""
        if res[11]:
            msg += f""", {res[11]}"""
        cursor.execute("SELECT Base FROM ChartInfo WHERE Id='{}' "
                       "ORDER BY FIELD(Difficulty,'绿','黄','红','紫','白')".format(id))
        res = cursor.fetchall()
        msg += f"""
定数："""
        base_list = [res[i][0] for i in range(len(res))]
        msg += ", ".join(base_list)
    except IndexError:
        msg = "歌曲不存在......"
    cursor.close()
    if os.path.exists("cover/{}.jpg".format(id)):
        img_path = f"file://{os.getcwd()}/cover/{id}.jpg"
    elif os.path.exists("cover/{}.png".format(id)):
        img_path = f"file://{os.getcwd()}/cover/{id}.png"
    else:
        img_path = ""
    return msg, img_path


