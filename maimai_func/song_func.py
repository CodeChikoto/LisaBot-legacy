import re
import os
import random
from tools.database import *
import json
from tools.shared_var import *


random.seed(2508)
cursor = Cursor()


def search_by_inner_level(user_in: str):
    regex = "定数查歌 " + difficulty_regex + "?([0-9]+\.[0-9])"
    difficulty, inner_level = re.match(regex, user_in.lower()).groups()
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
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
    regex = "等级查歌 " + difficulty_regex + "?([0-9]+\+?)"
    difficulty, level = re.match(regex, user_in.lower()).groups()
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
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
        [keyword] = re.match(regex, keyword).groups()
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
    [difficulty, level] = re.match("随歌 " + difficulty_regex + "\s?([0-9]+\+?)$", user_in.lower()).groups()
    # (难度)(数字)(+|)
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    amount = cursor.execute(f"SELECT Id FROM ChartDifficulty WHERE Level='{level}' "
                            f"AND Difficulty LIKE '{difficulty}'")
    rand_int = random.randint(0, amount - 1)
    if amount:
        [id] = cursor.fetchall()[rand_int]
        return select_song(f"id {id}")
    else:
        return "随机条件不对哦～", None


def random_by_inner_level(user_in: str):
    [difficulty, inner_level] = re.match("随歌 " + difficulty_regex + "\s?([0-9]+\.[0-9])", user_in.lower()).groups()
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！", ""
    difficulty = difficulty_alias[difficulty] if difficulty and difficulty in difficulty_alias else '%'
    amount = cursor.execute(f"SELECT Id FROM ChartDifficulty WHERE InnerLevel LIKE {inner_level} "
                            f"AND Difficulty LIKE '{difficulty}'")
    rand_int = random.randint(0, amount - 1)
    if amount:
        [id] = cursor.fetchall()[rand_int]
        return select_song(f"id {id}")
    else:
        return "随机条件不对哦～", "None"


def random_any(user_in: str):
    amount = cursor.execute(f"SELECT Id FROM SongInfo")
    rand_int = random.randint(0, amount - 1)
    id = cursor.fetchall()[rand_int][0]
    return select_song(f"id {id}")


def select_song(user_in: str):
    [id, version] = re.match("id ([0-9]+)\s?(.+)?", user_in).groups()
    version = "舞萌DX 2021" if not version else version
    cursor.execute(f"SELECT COUNT(DISTINCT Version) FROM ChartDifficulty WHERE Version LIKE '%{version}%'")
    if cursor.fetchone()[0] != 1:
        return "这是什么大版本呀？", ""
    cursor.execute(f"SELECT * FROM SongInfo WHERE Id={id}")
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
    with open("./cache/song_cover" + res[8], "wb") as cover:
        cover.write(res[7])
    cover.close()
    img_path = f"file://{os.getcwd()}/cache/song_cover" + res[8] if res[7] else ""
    cursor.execute(f"SELECT Level,InnerLevel FROM ChartDifficulty "
                   f"WHERE Id={id} AND Version LIKE '%{version}%'"
                   "ORDER BY FIELD(Difficulty,'Basic','Advanced',"
                   "'Expert','Master','Re:MASTER')")
    res = cursor.fetchall()
    level, inner_level = [data[0] for data in res], [str(data[1]) for data in res]
    msg += ",".join(level)
    msg += '\n定数：'
    msg += ",".join(inner_level)
    return msg, img_path


def add_alias_handle(user_in: str):
    regex = "增加别名 ([0-9]+) (.+)"
    [id, alias] = re.match(regex, user_in).groups()
    cursor.execute(f"INSERT IGNORE SongAlias (Id,Alias) VALUES ({id},'{alias}')")
    cursor.commit()
