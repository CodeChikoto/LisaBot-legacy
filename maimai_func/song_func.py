import re
import random
from math import ceil
from tools.shared_var import *
from tools.image import *
from io import StringIO

random.seed(2508)


def _format_song_list(res: list, page: int) -> str:
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
            msg += f"\n{song[0]}  {difficulty_short[song[1]]}  {song[2]}"
    return msg


def search_by_inner_level(user_in: str):
    regex = "定数查歌 " + difficulty_regex + "?([0-9]{1,2}\.[0-9])\s?([0-9]+)?"
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
    difficulty, inner_level, level = re.match("^随歌\s?" + difficulty_regex + "?([0-9]{1,2}\.[0-9])?([0-9]+\+?)?",
                                              user_in).groups()
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
        return select_song_chart(f"id {id}")
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
    regex = "(BPM|速度)查歌 ([0-9]+)\s?([0-9]+)?"
    _, bpm, page = re.match(regex, user_in.upper()).groups()
    page = 1 if not page else int(page)
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Id,Title FROM SongInfo WHERE BPM={bpm}")
    res = cursor.fetchall()
    conn.close()
    return _format_song_list(res, page)


def select_song_chart(user_in: str):
    [id, version] = re.match("id ([0-9]+)\s?(.+)?", user_in).groups()
    id = int(id)
    level_ver = "舞萌DX 2021" if not version else version.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    if cursor.execute(f"SELECT DISTINCT Version FROM ChartDifficulty WHERE Version LIKE '%{level_ver}%'") != 1:
        return "输入的大版本好像不太明确？", ""
    [level_ver] = cursor.fetchone()
    exist = cursor.execute(f"SELECT Title,Artist,BPM,ChartType,Genre,Version,ChinaVersion FROM SongInfo WHERE Id={id}")
    if not exist:
        return "歌曲不存在哦！", ""
    base_img = Image.open("./material/song_chart_bg/idpic-bg-lisa.png")
    base_draw = ImageDraw.Draw(base_img)
    bold18 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 18, encoding="utf-8")
    bold24 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 24, encoding="utf-8")
    bold26 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 26, encoding="utf-8")
    bold36 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 36, encoding="utf-8")
    medium26 = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 26, encoding="utf-8")
    heavy30 = ImageFont.truetype("./material/typeface/SourceHanSans_22.ttf", 30, encoding="utf-8")
    cover_img = Image.open(BytesIO(fetch_song_cover(id))).resize((103, 103))
    title, artist, bpm, chart_type, genre, version, china_version = cursor.fetchone()
    chart_type_img = Image.open("./material/chart_type/UI_TST_Infoicon_DeluxeMode.png").resize((100, 32)) \
        if chart_type == "DX" \
        else Image.open("./material/chart_type/UI_TST_Infoicon_StandardMode.png").resize((100, 32))
    base_img.paste(cover_img, (123, 89), mask=cover_img.split()[3])
    base_img.paste(chart_type_img, (260, 170), mask=chart_type_img.split()[3])
    limit = lambda text: text if bold36.getsize(text)[0] <= 684 else limit(text[:-1])
    title = limit(title)
    base_draw.text((264, 75), title, "#083060", font=bold36)
    base_draw.text((264, 125), artist, "#083060", font=bold24)
    base_draw.text((370, 164), f"ID {id}          {genre}          BPM {bpm}", "#083060", font=medium26)
    base_draw.text((864 - int(bold26.getsize(version)[0] / 2), 700), version, "#083060", font=bold26)
    base_draw.text((864 - int(bold26.getsize(china_version)[0] / 2), 758), china_version, "#083060", font=bold26)
    cursor.execute(f"SELECT Tap,Hold,Slide,Touch,Break,Charter FROM ChartInfo WHERE Id={id} "
                   f"ORDER BY FIELD(Difficulty,'Basic','Advanced','Expert','Master','Re:MASTER')")
    chart_info_list = cursor.fetchall()
    cursor.execute(f"SELECT Level,InnerLevel FROM ChartDifficulty WHERE Id={id} AND Version='{level_ver}' "
                   f"ORDER BY FIELD(Difficulty,'Basic','Advanced','Expert','Master','Re:MASTER')")
    chart_difficulty_list = cursor.fetchall()
    if not chart_difficulty_list:
        chart_difficulty_list = ((), (), (), (), ())
    base_draw.text((165 - int(bold18.getsize(level_ver)[0] / 2), 302), level_ver, "#083060", font=bold18)
    for x, chart_info, chart_difficulty in zip(range(315, 916, 150), chart_info_list, chart_difficulty_list):
        sum_notes = sum(chart_info[0:5] if chart_info[3] else chart_info[0:3] + chart_info[4:5])
        if chart_difficulty:
            base_draw.text((x - int(bold24.getsize(f"{chart_difficulty[0]} ({chart_difficulty[1]})")[0] / 2), 296),
                           f"{chart_difficulty[0]} ({chart_difficulty[1]})", "white" if x != 915 else "#BD31E4",
                           font=bold24)
        base_draw.text((x - int(heavy30.getsize(f"{sum_notes}")[0] / 2), 339), f"{sum_notes}", "#083060", font=heavy30)
        for i, y in enumerate((395, 444, 494, 544, 594)):
            if chart_info[i]:
                base_draw.text((x - int(medium26.getsize(f"{chart_info[i]}")[0] / 2), y), f"{chart_info[i]}", "#083060",
                               font=medium26)
    limit = lambda text: text if bold18.getsize(text)[0] <= 210 else limit(text[:-1])
    for charter, y in zip((chart[5] for chart in chart_info_list[2:]), (697, 737, 777)):
        base_draw.text((255, y), f"{limit(charter)}", "#083060", font=bold18)
    return "", str(image_to_base64(base_img), encoding="utf-8")


def add_alias_handle(user_in: str):
    regex = "增加别名 ([0-9]+) (.+)"
    [id, alias] = re.match(regex, user_in).groups()
    alias = alias.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"INSERT IGNORE SongAlias (Id,Alias) SELECT {id},'{alias}' FROM dual "
                   f"WHERE NOT EXISTS (SELECT Alias FROM SongAlias WHERE Alias LIKE '%{alias}%')")
    conn.commit()
    conn.close()


def show_alias_handle(user_in: str):
    regex = "查看别名 ([0-9]+)"
    [id] = re.match(regex, user_in).groups()
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Alias FROM SongAlias WHERE Id={id}")
    res = cursor.fetchall()
    if not res:
        return "真的有这首歌么？"
    else:
        return "该歌曲别名包括：" + "、".join([alias for [alias] in res])


def delete_alias_handle(user_in: str):
    regex = "删除别名 ([0-9]+) (.+)"
    [id, alias] = re.match(regex, user_in).groups()
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM SongAlias WHERE Id={id} AND Alias='{alias}'")
    conn.commit()
    conn.close()
    return "オーケー"
