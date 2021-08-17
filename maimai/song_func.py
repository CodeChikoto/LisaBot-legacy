"""
Error Code: 0 Succeeded, -1 Input Error, -2 Database Error
"""


import re
import pymysql
import os
from nonebot.adapters.cqhttp import Message, Event, Bot
import random

try:
    connection = pymysql.connect(host="127.0.0.1", user="root", password="Root-User",
                                 db="maimai", port=3306)
    random.seed(114514)
    print("Database succeeded!")
except TimeoutError:
    exit(-1)


def search_by_base(base, difficulty=None):
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


def search_by_level(level: str, difficulty=None):
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
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = res[:31]
    else:
        msg = "搜索结果："
    for song in res:
        msg += "\n{}  {}".format(song[0], song[1])
    cursor.close()
    return msg


def search_by_name(keyword: str):
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
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = res[:31]
    else:
        msg = "搜索结果："
    for song in res:
        msg += "\n{}  {}".format(song[0], song[1])
    cursor.close()
    return msg


def random_song(base=None, level=None, difficulty="%"):
    cursor = connection.cursor()
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
    cursor.close()
    return select_song(id)


def select_song(id: str):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM SongInfo WHERE Id='{}'".format(id))
    try:
        res = cursor.fetchall()[0]
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
        for i in range(len(res)):
            msg += res[i][0] + ", "
    except IndexError:
        msg = "歌曲不存在......"
    try:
        if os.path.exists("cover/{}.jpg".format(id)):
            file = f"file://{os.getcwd()}/cover/{id}.jpg"
        else:
            file = f"file://{os.getcwd()}/cover/{id}.png"
        final_msg = Message([
            {
                "type": "image",
                "data": {"file": f"{file}"}
            },
            {
                "type": "text",
                "data": {"text": msg}
            }
        ])
    except FileNotFoundError:
        final_msg = msg
    cursor.close()
    return final_msg

