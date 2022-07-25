import re
import random
from math import ceil
from models.mai_models import *
from tools.shared_var import *
from tools.image import *

random.seed(2508)


def _format_song_list(songs, page: int) -> str:
    if not songs:
        return "没有找到呢"
    total_page = int(ceil(len(songs) / 20))
    if page > total_page:
        return "你翻太多页啦"
    songs = songs[(page - 1) * 20:min(page * 20, len(songs))]
    msg = f"搜索结果第{page}/{total_page}页："
    try:
        for song in songs:
            msg += f"\n{song.id}  {difficulty_short[song.difficulty]}  {song.title}"
    except AttributeError:
        for song in songs:
            msg += f"\n{song.id}  {song.title}"
    finally:
        return msg


async def search_by_inner_level(user_in: str):
    regex = "定数查歌 " + difficulty_regex + "?([0-9]{1,2}\.[0-9])\s?([0-9]+)?"
    difficulty, inner_level, page = re.match(regex, user_in.lower()).groups()
    inner_level = float(inner_level)
    page = 1 if not page else int(page)
    if difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    songs = SongInfo. \
        select(SongInfo.id, ChartDifficulty.difficulty, SongInfo.title). \
        join(ChartDifficulty, on=(SongInfo.id == ChartDifficulty.id)). \
        where((ChartDifficulty.version == "舞萌DX2022") &
              (ChartDifficulty.inner_level.like(inner_level)) &
              (ChartDifficulty.difficulty ** difficulty)). \
        objects()
    return _format_song_list(songs, page)


async def search_by_artist(user_in: str):
    regex = "(曲师|艺术家|歌手)查歌 (.+)"
    _, keyword = re.match(regex, user_in).groups()
    keyword = keyword.strip()
    songs = SongInfo. \
        select(SongInfo.id, SongInfo.title). \
        where(SongInfo.artist.contains(keyword)). \
        objects()
    return _format_song_list(songs, 1)


async def search_by_level(user_in: str):
    regex = "等级查歌 " + difficulty_regex + "?([0-9]+\+?)\s?([0-9]+)?"
    difficulty, level, page = re.match(regex, user_in.lower()).groups()
    page = 1 if not page else int(page)
    if difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    songs = SongInfo. \
        select(SongInfo.id, ChartDifficulty.difficulty, SongInfo.title). \
        join(ChartDifficulty, on=(SongInfo.id == ChartDifficulty.id)). \
        where((ChartDifficulty.version == "舞萌DX2022") &
              (ChartDifficulty.level == level) &
              (ChartDifficulty.difficulty ** difficulty)). \
        objects()
    return _format_song_list(songs, page)


async def search_by_name(user_in: str):
    if "是什么歌" in user_in:
        regex = "(.+)是什么歌\s?([0-9]+)?$"
        keyword, page = re.match(regex, user_in).groups()
    else:
        regex = "(search|查歌|搜索) (.+)"
        _, keyword = re.match(regex, user_in).groups()
        page = 1
    page = 1 if not page else int(page)
    keyword = keyword.strip()
    songs = SongInfo. \
        select(SongInfo.id, SongInfo.title). \
        left_outer_join(SongAlias, on=(SongInfo.id == SongAlias.id)). \
        where(SongInfo.title.contains(keyword) | SongAlias.alias.contains(keyword)). \
        distinct(). \
        objects()
    return _format_song_list(songs, page)


async def random_by_aug(user_in: str):
    difficulty, inner_level, level = re.match("^随歌\s?" + difficulty_regex + "?([0-9]{1,2}\.[0-9])?([0-9]+\+?)?",
                                              user_in).groups()
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！"
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    if inner_level:
        charts = ChartDifficulty. \
            select(ChartDifficulty.id). \
            where((ChartDifficulty.inner_level.like(inner_level)) &
                  (ChartDifficulty.difficulty ** difficulty) &
                  (ChartDifficulty.version == '舞萌DX2022')). \
            objects()
    elif level:
        charts = ChartDifficulty. \
            select(ChartDifficulty.id). \
            where((ChartDifficulty.level == level) &
                  (ChartDifficulty.difficulty ** difficulty) &
                  (ChartDifficulty.version == '舞萌DX2022')). \
            objects()
    else:
        charts = ChartDifficulty. \
            select(ChartDifficulty.id.distinct()). \
            where(ChartDifficulty.version == '舞萌DX2022'). \
            objects()
    if charts:
        chart = random.choice(charts)
        return select_song_charts(f"id {chart.id}")
    else:
        return "随机条件不对哦～", None


async def search_by_notes_amount(user_in: str):
    regex = "^物量查歌 ([0-9]+)\s?([0-9]+)?"
    amount, page = re.match(regex, user_in).groups()
    page = 1 if not page else int(page)
    songs = SongInfo. \
        select(SongInfo.id, ChartInfo.difficulty, SongInfo.title). \
        join(ChartInfo, on=(SongInfo.id == ChartInfo.id)). \
        where((ChartInfo.touch.is_null()
               & (ChartInfo.tap + ChartInfo.hold + ChartInfo.slide + ChartInfo.break_ == amount)) |
              (~ChartInfo.touch.is_null() &
               (ChartInfo.tap + ChartInfo.hold + ChartInfo.slide + ChartInfo.break_ + ChartInfo.touch == amount))). \
        objects()
    return _format_song_list(songs, page)


async def search_by_bpm(user_in: str):
    regex = "(bpm|BPM|速度)查歌 ([0-9]+)\s?([0-9]+)?"
    _, bpm, page = re.match(regex, user_in.upper()).groups()
    page = 1 if not page else int(page)
    songs = SongInfo. \
        select(SongInfo.id, SongInfo.title). \
        where(SongInfo.bpm == bpm). \
        objects()
    return _format_song_list(songs, page)


async def select_song_charts(user_in: str):
    [id, version] = re.match("^id ([0-9]+)\s?(.+)?", user_in).groups()
    version = "舞萌DX2022" if not version else version.strip()
    song = SongInfo.get_or_none(SongInfo.id == id)
    if not song:
        return "歌曲不存在哦！", ""
    if not song.china_version:
        song.china_version = ""
    base_img = Image.open("./material/song_chart_bg/idpic-bg-lisa.png")
    base_draw = ImageDraw.Draw(base_img)
    bold18 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 18, encoding="utf-8")
    bold24 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 24, encoding="utf-8")
    bold26 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 26, encoding="utf-8")
    bold36 = ImageFont.truetype("./material/typeface/SourceHanSans_37.ttf", 36, encoding="utf-8")
    medium24 = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 24, encoding="utf-8")
    medium26 = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 26, encoding="utf-8")
    heavy30 = ImageFont.truetype("./material/typeface/SourceHanSans_22.ttf", 30, encoding="utf-8")
    cover_img = Image.open(BytesIO(song.cover)).resize((103, 103))
    chart_type_img = Image.open("./material/chart_type/UI_TST_Infoicon_DeluxeMode.png").resize((100, 32)) \
        if song.chart_type == "DX" \
        else Image.open("./material/chart_type/UI_TST_Infoicon_StandardMode.png").resize((100, 32))
    base_img.paste(cover_img, (123, 89))
    base_img.paste(chart_type_img, (260, 170), mask=chart_type_img.split()[3])
    limit = lambda text: text if bold36.getsize(text)[0] <= 684 else limit(text[:-1])
    title = limit(song.title)
    base_draw.text((264, 75), title, "#083060", font=bold36)
    limit = lambda text: text if medium24.getsize(text)[0] <= 700 else limit(text[:-1])
    artist = limit(song.artist)
    base_draw.text((264, 125), artist, "#083060", font=medium24)
    base_draw.text((370, 164), f"ID {id}          {song.genre}          BPM {song.bpm}", "#083060", font=medium26)
    base_draw.text((864 - int(bold26.getsize(song.version)[0] / 2), 700), song.version, "#083060", font=bold26)
    base_draw.text((864 - int(bold26.getsize(song.china_version)[0] / 2), 758), song.china_version,
                   "#083060", font=bold26)
    charts = ChartInfo.select().where(ChartInfo.id == id). \
        order_by(SQL("FIELD(Difficulty,'Basic','Advanced','Expert','Master','Re:MASTER')")).objects()
    charts_difficulties = ChartDifficulty.\
        select().\
        where((ChartDifficulty.id == id) & (ChartDifficulty.version == version)). \
        order_by(SQL("FIELD(Difficulty,'Basic','Advanced','Expert','Master','Re:MASTER')")).\
        objects()
    chart_difficulty_tuple = ((chart.level, chart.inner_level) for chart in charts_difficulties) \
        if charts_difficulties else ((), (), (), (), ())
    if charts_difficulties:
        base_draw.text((165 - int(bold18.getsize(charts_difficulties[0].version)[0] / 2), 302),
                       charts_difficulties[0].version, "#083060", font=bold18)
    for x, chart, difficulty in zip(range(315, 916, 150), charts, chart_difficulty_tuple):
        sum_notes = chart.tap + chart.hold + chart.slide + (chart.touch if chart.touch else 0) + chart.break_
        if difficulty:
            base_draw.text((x - int(bold24.getsize(f"{difficulty[0]} ({difficulty[1]})")[0] / 2), 296),
                           f"{difficulty[0]} ({difficulty[1]})", "white" if x != 915 else "#BD31E4", font=bold24)
        base_draw.text((x - int(heavy30.getsize(f"{sum_notes}")[0] / 2), 339), f"{sum_notes}", "#083060", font=heavy30)
        for i, y in zip((chart.tap, chart.hold, chart.slide, chart.touch, chart.break_), (395, 444, 494, 544, 594)):
            if i is None:
                continue
            if chart:
                base_draw.text((x - int(medium26.getsize(f"{i}")[0] / 2), y), f"{i}", "#083060", font=medium26)
    limit = lambda text: text if bold18.getsize(text)[0] <= 210 else limit(text[:-1])
    for charter, y in zip((chart.charter for chart in charts[2:]), (697, 737, 777)):
        base_draw.text((255, y), f"{limit(charter)}", "#083060", font=bold18)
    return "", str(image_to_base64(base_img), encoding="utf-8")


async def select_song(user_in: str):
    [id, version] = re.match("^ma?i?song ([0-9]+)\s?(.+)?", user_in).groups()
    version = "舞萌DX2022" if not version else version.strip()
    song = SongInfo.get_or_none(SongInfo.id == id)
    if not song:
        return "歌曲不存在哦！", ""
    text = f"""
ID: {song.id}
标题：{song.title}
艺术家：{song.artist}
BPM: {song.bpm}
谱面类型：{song.chart_type}
分类：{song.genre}
日服版本：{song.version}
国服版本：{song.china_version}"""
    img = Image.open(BytesIO(song.cover))
    charts_difficulties = ChartDifficulty.select(ChartDifficulty.level, ChartDifficulty.inner_level). \
        where((ChartDifficulty.id == id) & (ChartDifficulty.version == version)). \
        order_by(SQL("FIELD(Difficulty,'Basic','Advanced','Expert','Master','Re:MASTER')")). \
        objects()
    text += ("\n等级：" + ",".join([f"{chart.level}" for chart in charts_difficulties]))
    text += ("\n定数：" + ",".join([f"{chart.inner_level}" for chart in charts_difficulties]))
    return text, str(image_to_base64(img), encoding="utf-8")


async def add_alias(user_in: str):
    regex = "增加别名 ([0-9]+) (.+)"
    [id, alias] = re.match(regex, user_in).groups()
    alias = alias.strip()
    try:
        SongAlias.create(id=id, alias=alias).save()
    except KeyError:
        return "别名已存在或 ID 不存在呢～"
    return "わかった！"


async def find_alias(user_in: str):
    regex = "查看别名 ([0-9]+)"
    [id] = re.match(regex, user_in).groups()
    aliases = SongAlias.select().where(SongAlias.id == id).objects()
    if not aliases:
        return "真的有这首歌么？"
    else:
        return "该歌曲别名包括：" + "、".join([alias.alias for alias in aliases])


async def delete_alias(user_in: str):
    regex = "删除别名 ([0-9]+) (.+)"
    [id, alias] = re.match(regex, user_in).groups()
    alias = alias.strip()
    SongAlias.delete().where((SongAlias.id == id) & (SongAlias.alias == alias))
    return "オーケー"
