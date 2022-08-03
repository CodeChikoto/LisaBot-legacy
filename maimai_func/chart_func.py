import re
import random
import os
from typing import Any
from models.mai_models import *
import maimai_func.song_func
from tools.image import *
from tools.shared_var import *
from math import ceil
from multiprocessing import Process, Queue

random.seed(2508)


def _check_combo(user_chart):
    if all(miss[-1] == 0 for miss in user_chart):
        if all(good[-2] == 0 for good in user_chart):
            if all(great[-3] == 0 for great in user_chart):
                state = "AP+" if user_chart[-1][1] == 0 else "AP"
            else:
                state = "FC+"
        else:
            state = "FC"
    else:
        state = None
    if state == "AP+":
        return "やりましたおめでとうございます"
    elif state == "AP":
        return "AP だよ！目に害があった！"
    elif state == "FC+" or state == "FC":
        return f"{state} 哇哦～"
    else:
        return ""


async def cal_achievements_range(user_in: str):
    regex = f"达成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+),([0-9]+)"
    groups = re.match(regex, user_in).groups()
    difficulty = difficulty_alias[groups[0]] if groups[0] in difficulty_alias else groups[0]
    id = groups[1]
    chart = ChartInfo.get_or_none(ChartInfo.id == id, ChartInfo.difficulty == difficulty)
    if not chart:
        return "没有这个谱面捏"
    chart.touch = 0 if not chart.touch else chart.touch
    total_basic = 1 * chart.tap + 2 * chart.hold + 3 * chart.slide + 5 * chart.break_ + chart.touch
    total_ex = chart.break_
    user_chart = [[int(groups[2]), int(groups[3]), int(groups[4])],
                  [int(groups[5]), int(groups[6]), int(groups[7])],
                  [int(groups[8]), int(groups[9]), int(groups[10])],
                  [int(groups[11]), int(groups[12]), int(groups[13])],
                  [int(groups[14]), int(groups[15]), int(groups[16]), int(groups[17])]]
    user_basic = 0
    # check
    for i, amount in enumerate((chart.tap, chart.hold, chart.slide, chart.touch, chart.break_)):
        if not 0 <= sum(user_chart[i]) <= amount:
            return "输入数量不对哦！"
        user_chart[i].insert(0, amount - sum(user_chart[i]))
    for i, full in enumerate([1, 2, 3, 1]):
        for j, ratio in enumerate([1, 0.8, 0.5]):
            user_basic += user_chart[i][j] * full * ratio
    max_user_basic = user_basic + 5 * (user_chart[-1][0] + user_chart[-1][1]) + \
                     4 * user_chart[-1][2] + 2 * user_chart[-1][3]
    min_user_basic = user_basic + 5 * (user_chart[-1][0] + user_chart[-1][1]) + \
                     2.5 * user_chart[-1][2] + 2 * user_chart[-1][3]
    max_user_ex = user_chart[-1][0] + 0.75 * user_chart[-1][1] + \
                  0.4 * user_chart[-1][2] + 0.3 * user_chart[-1][3]
    min_user_ex = user_chart[-1][0] + 0.5 * user_chart[-1][1] + \
                  0.4 * user_chart[-1][2] + 0.3 * user_chart[-1][3]
    max_achie = max_user_basic / total_basic * 100 + max_user_ex / total_ex
    min_achie = min_user_basic / total_basic * 100 + min_user_ex / total_ex
    return f"{max_achie:.4f}% ~ {min_achie:.4f}%\n" \
           f"结果可能存在略微偏差\n" + _check_combo(user_chart)


async def cal_break_dist(user_in: str):
    regex = f"绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+\.[0-9]+)"
    groups = re.match(regex, user_in).groups()
    difficulty = difficulty_alias[groups[0]] if groups[0] in difficulty_alias else groups[0]
    id = groups[1]
    ans = []
    chart = ChartInfo.get_or_none(ChartInfo.id == id, ChartInfo.difficulty == difficulty)
    if not chart:
        return "没有这个谱面捏"
    chart.touch = 0 if not chart.touch else chart.touch
    total_basic = 1 * chart.tap + 2 * chart.hold + 3 * chart.slide + 5 * chart.break_ + 1 * chart.touch
    total_ex = chart.break_
    user_chart = [[int(groups[2]), int(groups[3]), int(groups[4])],
                  [int(groups[5]), int(groups[6]), int(groups[7])],
                  [int(groups[8]), int(groups[9]), int(groups[10])],
                  [int(groups[11]), int(groups[12]), int(groups[13])],
                  [int(groups[14]), int(groups[15]), int(groups[16]), int(groups[17])]]
    user_basic = 0
    # check
    for i, amount in enumerate((chart.tap, chart.hold, chart.slide, chart.touch, chart.break_)):
        if not 0 <= sum(user_chart[i]) <= amount:
            return "输入数量不对哦！"
        user_chart[i].insert(0, amount - sum(user_chart[i]))
    for i, full in enumerate([1, 2, 3, 1]):
        for j, ratio in enumerate([1, 0.8, 0.5]):
            user_basic += user_chart[i][j] * full * ratio
    # break perfect, ex 0.75/0.5
    for i in range(user_chart[-1][1] + 1):
        # break great, basic 4/3/2.5
        # j - 4, k - 3, -j-k - 2.5
        for j in range(user_chart[-1][2] + 1):
            for k in range(user_chart[-1][2] - j + 1):
                user_basic_trial = user_basic + 5 * (user_chart[-1][0] + user_chart[-1][1]) + 4 * j + 3 * k + \
                                   2.5 * (user_chart[-1][2] - j - k) + 2 * user_chart[-1][3]
                user_ex = user_chart[-1][0] + 0.75 * i + 0.5 * (user_chart[-1][1] - i) + \
                          0.4 * user_chart[-1][2] + 0.3 * user_chart[-1][3]
                if re.match(groups[18], str(user_basic_trial / total_basic * 100 + user_ex / total_ex)):
                    # [p 0.75, p 0.5, gr 4, gr 3, gr 2.5]
                    ans.append([i, user_chart[-1][1] - i, j, k, user_chart[-1][2] - j - k])
    if not ans:
        return "可能性がない......", None
    msg = f"Break Perfect 分为0.75/0.5额外分，并且都有5基础分。\n" \
          f"Break Great 分为4/3/2.5基础分，并且都有0.4额外分。"
    for case in ans:
        msg += f"\nP0.75:{case[0]}  P0.5:{case[1]}  Gr4:{case[2]}  Gr3:{case[3]}  Gr2.5:{case[4]}"
    return _check_combo(user_chart), str(image_to_base64(text_to_image(msg)), encoding="utf-8")


async def select_chart(user_in: str):
    global difficulty_alias, chart_regex
    regex = "ma?i?chart " + difficulty_regex + "([0-9]+)\s?(.+)?"
    difficulty, id, version = re.match(regex, user_in.lower()).groups()
    if not difficulty or difficulty not in difficulty_alias:
        return "难度输入不对哦！", ""
    version = "舞萌DX2022" if not version else version.strip()
    amount = ChartDifficulty. \
        select(fn.COUNT(ChartDifficulty.version.distinct()).alias('count')). \
        where(ChartDifficulty.version ** version). \
        get()
    if not amount.count:
        return "版本不正确哦！", ""
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    chart = ChartInfo.select(ChartInfo, SongInfo, ChartDifficulty). \
        join(ChartDifficulty,
             on=((ChartInfo.id == ChartDifficulty.id) & (ChartInfo.difficulty == ChartDifficulty.difficulty))). \
        switch(ChartInfo). \
        join(SongInfo, on=(SongInfo.id == ChartInfo.id)). \
        where((ChartInfo.id == id) &
              (ChartInfo.difficulty == difficulty) &
              (ChartDifficulty.version == version)). \
        get()
    if not chart:
        return "谱面不存在哟！检查下 ID 或者难度～", ""
    chart.touch = 0 if not chart.touch else chart.touch
    msg = f"""
标题：{chart.songinfo.title}
ID: {chart.songinfo.id}
谱面类型：{chart.songinfo.chart_type}
BPM: {chart.songinfo.bpm}
难度：{chart.difficulty}
等级：{chart.chartdifficulty.level}
内部等级：{chart.chartdifficulty.inner_level}
Tap: {chart.tap}
Hold: {chart.hold}
Slide: {chart.slide}
Touch: {chart.touch}
谱师：{chart.charter}
定级版本：{chart.chartdifficulty.version}"""
    img = Image.open(BytesIO(chart.songinfo.cover))
    return msg, str(image_to_base64(img), encoding="utf-8")


async def random_chart(user_in: str):
    regex = r"我要大战(.+)"
    [keyword] = re.match(regex, user_in).groups()
    charts = ChartInfo. \
        select(). \
        join(ChartDifficulty,
             on=(ChartInfo.id == ChartDifficulty.id & ChartInfo.difficulty == ChartDifficulty.difficulty)). \
        where((ChartDifficulty.version == "舞萌DX2022") & (ChartInfo.charter ** f'%{keyword}%')). \
        objects()
    if charts:
        chart = random.choice(charts)
        return await maimai_func.song_func.select_song_charts(f"id {chart.id}")
    else:
        return "有这位谱师嘛？", None


async def get_achievements_line(user_in: str):
    regex = "(达成率|分数)线 " + difficulty_regex + "([0-9]+)\s?(0\+|100|101\-)?\s?(.+)?"
    _, difficulty, id, mode, version = re.match(regex, user_in.lower()).groups()
    version = "舞萌DX2022" if not version else version.strip()
    if not difficulty or difficulty not in difficulty_alias:
        return "难度输入不对哦！", None
    difficulty = difficulty_alias[difficulty]
    mode = "101-" if not mode else mode
    chart = ChartInfo.get_or_none(ChartInfo.id == id, ChartInfo.difficulty == difficulty)
    if not chart:
        return "谱面不存在哦～", None
    chart.touch = 0 if not chart.touch else chart.touch
    total_base = 1 * chart.tap + 2 * chart.hold + 3 * chart.slide + 5 * chart.break_ + 1 * chart.touch
    total_ex = chart.break_
    note_score, judge_coef, ans = [1, 2, 3, 1], [1, 1, 0.8, 0.5, 0], []
    if mode == "101-":
        base_pic = Image.open("./material/achi_line_bg/101-reduce-lisa.png")
        for i, score in enumerate(note_score):
            ans.append([])
            if not chart.touch and i == 3:
                continue
            for coef in judge_coef:
                ans[i].append(-((score - score * coef) / total_base * 100))
        ans.append([0.0, -0.25 / total_ex, -0.5 / total_ex, -1 / total_base * 100 - 0.6 / total_ex,
                    -2 / total_base * 100 - 0.6 / total_ex, -2.5 / total_base * 100 - 0.6 / total_ex,
                    -3 / total_base * 100 - 0.7 / total_ex, -5 / total_base * 100 - 1 / total_ex])
    elif mode == "0+":
        base_pic = Image.open("./material/achi_line_bg/0-plus-lisa.png")
        for i, score in enumerate(note_score):
            ans.append([])
            if not chart.touch and i == 3:
                continue
            for coef in judge_coef:
                ans[i].append(score * coef / total_base * 100)
        ans.append([1 / total_ex + 5 / total_base * 100, 0.75 / total_ex + 5 / total_base * 100,
                    0.5 / total_ex + 5 / total_base * 100, 4 / total_base * 100 + 0.4 / total_ex,
                    3 / total_base * 100 + 0.4 / total_ex, 2.5 / total_base * 100 + 0.4 / total_ex,
                    2 / total_base * 100 + 0.3 / total_ex, 0])
    else:
        base_pic = Image.open("./material/achi_line_bg/100-lisa.png")
        for i, score in enumerate(note_score):
            ans.append([])
            if not chart.touch and i == 3:
                continue
            for coef in judge_coef:
                ans[i].append(-((score - score * coef) / total_base * 100))
        ans.append([1 / total_ex, 0.75 / total_ex, 0.5 / total_ex, -1 / total_base * 100 + 0.4 / total_ex,
                    -2 / total_base * 100 + 0.4 / total_ex, -2.5 / total_base * 100 + 0.4 / total_ex,
                    -3 / total_base * 100 + 0.3 / total_ex, -5 / total_base * 100])
    chart_diff = ChartDifficulty. \
        select(ChartDifficulty.inner_level). \
        where(ChartDifficulty.id == id,
              ChartDifficulty.difficulty == difficulty,
              ChartDifficulty.version == version). \
        get_or_none()
    inner_level = chart_diff.inner_level if chart_diff else ""
    title = SongInfo.select(SongInfo.title).where(SongInfo.id == id).get().title
    base_drawer = ImageDraw.Draw(base_pic)
    cover_frame = Image.open(f"./material/difficulty_frame/UI_UPE_MusicJacket_Base_"
                             f"{difficulty_file[difficulty]}.png").resize((146, 133))
    base_pic.paste(cover_frame, (101, 73), mask=cover_frame.split()[3])
    cover_img = Image.open(BytesIO(fetch_song_cover(id))).resize((103, 103))
    base_pic.paste(cover_img, (123, 89), mask=cover_img.split()[3])
    title_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 36, encoding="utf-8")
    limit = lambda text: text if title_font.getsize(text)[0] <= 680 else limit(text[:-1])
    title = limit(title)
    base_drawer.text((264, 75), title, "#083060", font=title_font)
    info_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 22, encoding="utf-8")
    base_drawer.text((264, 135), f"{difficulty}  {inner_level}            ID: {id}            Notes: "
                                 f"{sum((chart.tap, chart.hold, chart.slide, chart.touch, chart.break_))}",
                     f"#083060", font=info_font)
    for x, note in zip((314, 470, 611, 770, 920), (chart.tap, chart.hold, chart.slide, chart.touch, chart.break_)):
        base_drawer.text((x, 171), f"{note if note else '-'}", "#083060", font=info_font)
    for i, y in enumerate((337, 383, 428, 473)):
        if not chart.touch and i == 3:
            continue
        for j, x in enumerate((275, 437, 632, 795, 925)):
            if ans[i][j] < 0:
                base_drawer.text((x - int(info_font.getsize(f"{ans[i][j]:.5f}%")[0] / 2), y),
                                 f"{ans[i][j]:.5f}%", "#083060", font=info_font)
            elif ans[i][j] > 0:
                base_drawer.text((x - int(info_font.getsize(f"+{ans[i][j]:.5f}%")[0] / 2), y),
                                 f"+{ans[i][j]:.5f}%", "#FF3000", font=info_font)
    for i, (x, y) in enumerate(((275, 547), (470, 522), (470, 573), (665, 513), (665, 548), (665, 582),
                                (795, 547), (925, 547))):
        if ans[4][i] < 0:
            base_drawer.text((x - int(info_font.getsize(f"{ans[4][i]:.5f}%")[0] / 2), y),
                             f"{ans[4][i]:.5f}%", "#083060", font=info_font)
        elif ans[4][i] > 0:
            base_drawer.text((x - int(info_font.getsize(f"+{ans[4][i]:.5f}%")[0] / 2), y),
                             f"+{ans[4][i]:.5f}%", "#FF3000", font=info_font)
    great_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 23, encoding="utf-8")
    for (i, x), aim_achi in zip(enumerate((274, 385, 494, 604, 714, 824, 934)), (100.5, 100, 99.5, 99, 98, 97, 80)):
        allow_great = int((101 - aim_achi) / 100 * total_base * 5)
        base_drawer.text((x - int(great_font.getsize(f"{allow_great}")[0] / 2), 743), f"{allow_great}",
                         "#083060", font=great_font)
    if mode == "0+":
        break_equal_list = [(ans[-1][0] - ans[-1][i]) / (ans[0][0] - ans[0][2]) for i in range(1, 8)]
    elif mode == "101-":
        break_equal_list = [ans[-1][i] / ans[0][2] for i in range(1, 8)]
    else:
        break_equal_list = [(ans[-1][i] - ans[-1][0]) / ans[0][2] for i in range(1, 8)]
    for (i, x), break_equal in zip(enumerate((274, 385, 494, 604, 714, 824, 934)), break_equal_list):
        base_drawer.text((x - int(great_font.getsize(f"{break_equal:.4f}")[0] / 2), 930), f"{break_equal:.4f}",
                         "#083060", font=great_font)
    return "", str(image_to_base64(base_pic), encoding="utf-8")


# return: text, image path
async def get_version_plates(user_in: str):

    regex = "^牌子(条件|列表)\s?(.+)?"
    _, ver = re.match(regex, user_in).groups()
    if ver not in plate_ver_file.keys():
        return f"使用方法是：牌子条件 [版本简称]\n版本简称包含如下：{'、'.join(plate_ver_file.keys())}", ""
    if os.path.exists(f"./material/plate_requirement/Lisa/{plate_ver_file[ver]}-lisa.png"):
        return "", str(image_to_base64(Image.open(f"{os.getcwd()}/material/plate_requirement/Lisa/"
                                                  f"{plate_ver_file[ver]}-lisa.png")), encoding="utf-8")
    else:
        return "该版本牌子还没有上线～", ""


def cal_single_rating_line(user_in: str) -> str:
    achi_rank_coef_dict = {"SSS+": 14, "SSSp": 14, "SSS": 13.5, "SS+": 13.2, "SSp": 13.2, "SS": 13.0,
                           "S+": 12.7, "Sp": 12.7, "S": 12.5}

    def _cal_single_rating(achievements_level: str, inner_level: float, achievements: float) -> int:
        achievements = 100.5 if achievements > 100.5 else achievements
        return int(achievements / 100 * achi_rank_coef_dict[achievements_level] * float(inner_level))

    def _rating_to_achievement(achievements_level: str, single_rating: int, inner_level: float) -> Any:
        achi_rank_range_dict = {"SSS+": (101, 100.5), "SSSp": (100.4999, 100.0000), "SSS": (100.4999, 100.0000),
                               "SS+": (99.9999, 99.5000), "SSp": (99.9999, 99.5000), "SS": (99.4999, 99.0000),
                               "S+": (98.9999, 98.0000), "Sp": (98.9999, 98.0000), "S": (97.9999, 97.0000)}
        trial_achievements = single_rating / inner_level / achi_rank_coef_dict[achievements_level] * 100
        up, down = achi_rank_range_dict[achievements_level]
        return trial_achievements if down <= trial_achievements <= up else None

    ans = set()
    regex = "^单曲(rating|ra) ([0-9]{1,2}\.[0-9])"
    _, inner_level = re.match(regex, user_in.lower()).groups()
    inner_level = float(inner_level)
    if not 1.0 <= inner_level <= 15.0:
        return "真的有这个定数嘛？"
    for achievements_level in achievements_ranks.keys():
        if achievements_level == "AAA":
            break
        achievements = achievements_ranks[achievements_level]
        single_rating = _cal_single_rating(achievements_level, inner_level, achievements)
        for trial_single_rating in range(single_rating + 2, single_rating, -1):
            if achievements == 100.5:
                break
            trial_achievements = _rating_to_achievement(achievements_level, trial_single_rating, inner_level)
            if trial_achievements:
                ans.add((trial_achievements, trial_single_rating))
        ans.add((achievements, single_rating))
    ans = sorted(tuple(ans), key=lambda x: x[0], reverse=True)
    return f"定数{inner_level}的单曲 rating\n" + "\n".join([f"{ra}: {achi:03.4f}%" for achi, ra in ans])
