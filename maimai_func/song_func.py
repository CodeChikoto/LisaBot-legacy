import re
import os
import random
from math import ceil

from tools.shared_var import *

random.seed(2508)


def _format_song_list(res: list, page: int) -> str:
    def _get_difficulty_short(difficulty: str):
        if difficulty == "Basic":
            return "BSC"
        elif difficulty == "Advanced":
            return "ADV"
        elif difficulty == "Expert":
            return "EXP"
        elif difficulty == "Master":
            return "MST"
        elif difficulty == "Re:MASTER":
            return "REM"

    if not res:
        return "没有找到呢"
    total_page = int(ceil(len(res) / 20))
    if page > total_page:
        return "你翻太多页啦"
    res = res[(page - 1) * 20:min(page * 20, len(res))]
    msg = f"搜索结果第{page}/{total_page}页："
    if len(res[0]) == 2:
        for song in res:
            msg += f"\n{song[0]}  {song[1]}"
    else:
        for song in res:
            msg += f"\n{song[0]}  {_get_difficulty_short(song[1])}  {song[2]}"
    return msg


def search_by_inner_level(user_in: str):
    regex = "定数查歌 " + difficulty_regex + "?([0-9]+\.[0-9])\s?([0-9]+)?"
    difficulty, inner_level, page = re.match(regex, user_in.lower()).groups()
    page = 1 if not page else int(page)
    if difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT SI.Id,CD.Difficulty,SI.Title FROM SongInfo SI JOIN ChartDifficulty CD "
                   f"ON SI.Id=CD.Id WHERE CD.InnerLevel LIKE {inner_level} AND CD.Difficulty LIKE '{difficulty}' "
                   f"AND CD.Version='舞萌DX 2021'")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, page)


def search_by_artist(user_in: str):
    regex = "(曲师|艺术家|歌手)查歌 (.+)"
    _, keyword = re.match(regex, user_in).groups()
    keyword = keyword.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Id,Title FROM SongInfo WHERE Artist LIKE '%{keyword}%'")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, 1)


def search_by_level(user_in: str):
    regex = "等级查歌 " + difficulty_regex + "?([0-9]+\+?)\s?([0-9]+)?"
    difficulty, level, page = re.match(regex, user_in.lower()).groups()
    page = 1 if not page else int(page)
    if difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT SI.Id,CD.Difficulty,SI.Title FROM SongInfo SI JOIN ChartDifficulty CD "
                   f"ON SI.Id=CD.Id WHERE CD.Level='{level}' AND CD.Difficulty LIKE '{difficulty}' "
                   f"AND CD.Version='舞萌DX 2021'")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, page)


def search_by_name(user_in: str):
    if "是什么歌" in user_in:
        regex = "(.+)是什么歌\s?([0-9]+)?$"
        keyword, page = re.match(regex, user_in).groups()
    else:
        regex = "(search|查歌|搜索) (.+)"
        _, keyword = re.match(regex, user_in).groups()
        page = 1
    page = 1 if not page else int(page)
    keyword = keyword.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT Id,Title FROM SongInfo WHERE Title LIKE '%{keyword}%' "
                   f"OR Id IN (SELECT Id FROM SongAlias WHERE Alias='{keyword}')")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, page)


def random_by_aug(user_in: str):
    try:
        difficulty, inner_level, level = re.match("^随歌\s?" + difficulty_regex + "([0-9]+\.[0-9])?([0-9]+\+?)?",
                                                  user_in).groups()
    except AttributeError:
        difficulty, inner_level, level = None, None, None
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    if inner_level:
        amount = cursor.execute(f"SELECT Id FROM ChartDifficulty WHERE InnerLevel LIKE {inner_level} "
                                f"AND Difficulty LIKE '{difficulty}' AND Version='舞萌DX 2021'")
    elif level:
        amount = cursor.execute(f"SELECT Id FROM ChartDifficulty WHERE Level='{level}' "
                                f"AND Difficulty LIKE '{difficulty}' AND Version='舞萌DX 2021'")
    else:
        amount = cursor.execute(f"SELECT Id FROM SongInfo")
    if amount:
        rand_int = random.randint(0, amount - 1)
        [id] = cursor.fetchall()[rand_int]
        conn.close()
        return select_song(f"id {id}")
    else:
        conn.close()
        return "随机条件不对哦～", None


def search_by_notes_amount(user_in: str):
    regex = "^物量查歌 ([0-9]+)\s?([0-9]+)?"
    amount, page = re.match(regex, user_in).groups()
    page = 1 if not page else int(page)
    amount = int(amount)
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT SI.Id,CI.Difficulty,SI.Title FROM SongInfo SI JOIN ChartInfo CI ON SI.Id=CI.Id "
                   f"AND CI.Tap+CI.Hold+CI.Slide+CI.Touch+CI.Break={amount} AND CI.Touch IS NOT NULL "
                   f"UNION SELECT SI.Id,CI.Difficulty,SI.Title FROM SongInfo SI JOIN ChartInfo CI "
                   f"ON SI.Id=CI.Id AND CI.Tap+CI.Hold+CI.Slide+CI.Break={amount} AND CI.Touch IS NULL")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, page)


def search_by_bpm(user_in: str):
    regex = "(bpm|BPM|速度)查歌 ([0-9]+)\s?([0-9]+)?"
    _, bpm, page = re.match(regex, user_in.upper()).groups()
    page = 1 if not page else int(page)
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Id,Title FROM SongInfo WHERE BPM={bpm}")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, page)


def select_song(user_in: str):
    [id, version] = re.match("id ([0-9]+)\s?(.+)?", user_in).groups()
    version = "舞萌DX 2021" if not version else version
    version = version.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(DISTINCT Version) FROM ChartDifficulty WHERE Version LIKE '%{version}%'")
    if cursor.fetchone()[0] != 1:
        return "这是什么大版本呀？", ""
    cursor.execute(f"SELECT Id,Title,Artist,BPM,ChartType,Genre,Version,Cover,ImageExt FROM SongInfo WHERE Id={id}")
    res = cursor.fetchone()
    if not res:
        return "好像没有这首歌", ""
    msg = f"""
ID: {res[0]}
标题：{res[1]}
艺术家：{res[2]}
BPM: {res[3]}
谱面类型：{res[4]}
分类：{res[5]}
收录版本：{res[6]}
等级："""
    if res[7]:
        with open(f"./cache/{res[0]}{res[8]}", "wb") as cover:
            cover.write(res[7])
        cover.close()
    img_path = f"file://{os.getcwd()}/cache/{res[0]}{res[8]}" if res[7] else ""
    cursor.execute(f"SELECT Level,InnerLevel FROM ChartDifficulty WHERE Id={id} AND Version LIKE '%{version}%'"
                   "ORDER BY FIELD(Difficulty,'Basic','Advanced','Expert','Master','Re:MASTER')")
    res = cursor.fetchall()
    level, inner_level = [data[0] for data in res], [str(data[1]) for data in res]
    msg += ",".join(level)
    msg += '\n定数：'
    msg += ",".join(inner_level)
    conn.close()
    return msg, img_path


def add_alias_handle(user_in: str):
    regex = "增加别名 ([0-9]+) (.+)"
    [id, alias] = re.match(regex, user_in).groups()
    alias = alias.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE SongAlias (Id,Alias) VALUES (%s,%s)", (id, alias))
    conn.commit()
    conn.close()

