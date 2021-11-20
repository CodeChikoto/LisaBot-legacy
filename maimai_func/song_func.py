import re
import os
import random
from interact_func.send_help import *
from tools.database import *
import json

with open("./text/difficulty_alias.json", "r") as file:
    difficulty_alias = json.load(file)
    chart_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")(.*)"
    difficulty_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")"
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
                   f"(SELECT Id FROM ChartDifficulty WHERE InnerLevel LIKE {inner_level} AND "
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
                   f"(SELECT Id FROM ChartDifficulty WHERE Level='{level}' AND "
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
    cursor.execute(f"SELECT DISTINCT Id,Title FROM SongInfo WHERE Title LIKE '%{keyword}%' "
                   f"OR Id IN (SELECT Id FROM SongAlias WHERE Alias='{keyword}')")
    res = cursor.fetchall()
    if len(res) > 30:
        msg = "结果过多，仅显示30条："
        res = random.sample(res, 30)
    else:
        msg = "搜索结果："
    for song in res:
        msg += f"\n{song[0]}  {song[1]}"
    return msg


def random_by_level(user_in: str):
    if '.' in user_in:
        return "", None
    # (难度)(数字)(+|)
    groups = re.match(r"随歌 " + difficulty_regex + r"([0-9]+)([^\d\.])", user_in).groups()
    difficulty, level = difficulty_alias[groups[0]] if groups[0] and groups[0] in difficulty_alias else '%', \
                        groups[1]
    if groups[2] == '+':
        level += '+'
    amount = cursor.execute(f"SELECT Id FROM ChartDifficulty WHERE Level='{level}' "
                            f"AND Difficulty LIKE '{difficulty}'")
    rand_int = random.randint(0, amount - 1)
    try:
        id = cursor.fetchall()[rand_int][0]
        return select_song(str(id))
    except ValueError:
        return "随机条件不对哦～", None


def random_by_inner_level(user_in: str):
    groups = re.match(r"随歌 " + difficulty_regex + r"([0-9]+)(\.)([0-9])", user_in).groups()
    difficulty, inner_level = difficulty_alias[groups[0]] if groups[0] and groups[0] in difficulty_alias else '%', \
                              groups[1] + groups[2] + groups[3]
    amount = cursor.execute(f"SELECT Id FROM ChartDifficulty WHERE InnerLevel LIKE {inner_level} "
                            f"AND Difficulty LIKE '{difficulty}'")
    rand_int = random.randint(0, amount - 1)
    try:
        id = cursor.fetchall()[rand_int][0]
        return select_song(str(id))
    except ValueError:
        return "随机条件不对哦～", None


def random_any(user_in: str):
    if user_in == "help":
        return send_help("random_song"), None
    amount = cursor.execute(f"SELECT Id FROM SongInfo")
    rand_int = random.randint(0, amount - 1)
    id = cursor.fetchall()[rand_int][0]
    return select_song(str(id))


def select_song(user_in: str):
    try:
        args = user_in.split()
        id, version = args[0], args[1] if len(args) == 2 else "舞萌DX 2021"
        cursor.execute(f"SELECT * FROM SongInfo WHERE Id={id}")
        res = cursor.fetchone()
        msg = f"""
ID: {res[0]}
标题：{res[1]}
艺术家：{res[2]}
BPM: {res[3]}
谱面类型：{res[4]}
分类：{res[4]}
收录版本：{res[5]}
等级："""
        with open("./temp" + res[8], "wb") as cover:
            cover.write(res[7])
        cover.close()
        img_path = f"file://{os.getcwd()}/temp" + res[8] if res[7] else ""
        cursor.execute(f"SELECT Level,InnerLevel FROM ChartDifficulty "
                       f"WHERE Id={id} AND Version LIKE '%{version}%'"
                       "ORDER BY FIELD(Difficulty,'Basic','Advanced',"
                       "'Expert','Master','Re:Master')")
        res = cursor.fetchall()
        level, inner_level = [data[0] for data in res], [str(data[1]) for data in res]
        msg += ",".join(level)
        msg += '\n定数：'
        msg += ",".join(inner_level)
    except IndexError:
        msg, img_path = "歌曲不存在......", ""
    return msg, img_path


def add_alias_handle(user_in: str) -> bool:
    try:
        id, alias = user_in.split()
        cursor.execute(f"INSERT INTO SongAlias (Id,Alias) VALUES ({id},'{alias}')")
        cursor.commit()
        return True
    except Exception:
        pass
    return False
