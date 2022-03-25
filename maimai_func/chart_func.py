import re
import random
import os
from typing import Any
from tools.get_player_data import *
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


def cal_achie_range(user_in: str):
    regex = f"达成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+),([0-9]+)"
    groups = re.match(regex, user_in).groups()
    difficulty = difficulty_alias[groups[0]] if groups[0] in difficulty_alias else groups[0]
    id = groups[1]
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                   f"WHERE Difficulty='{difficulty}' AND Id={id}")
    chart_data = cursor.fetchone()
    conn.close()
    if chart_data:
        total_basic = 1 * chart_data[0] + 2 * chart_data[1] + 3 * chart_data[2] + 5 * chart_data[4]
        total_basic += 1 * chart_data[3] if chart_data[3] else 0
        total_ex = chart_data[4]
        user_chart = [[int(groups[2]), int(groups[3]), int(groups[4])],
                      [int(groups[5]), int(groups[6]), int(groups[7])],
                      [int(groups[8]), int(groups[9]), int(groups[10])],
                      [int(groups[11]), int(groups[12]), int(groups[13])],
                      [int(groups[14]), int(groups[15]), int(groups[16]), int(groups[17])]]
        user_basic = 0
        # check
        for i, amount in enumerate(chart_data):
            if not amount:
                continue
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
    else:
        return "没有这个谱面捏"


def cal_break_dist(user_in: str):
    regex = f"绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+),([0-9]+) " \
            f"([0-9]+.[0-9]+)"
    groups = re.match(regex, user_in).groups()
    difficulty = difficulty_alias[groups[0]] if groups[0] in difficulty_alias else groups[0]
    id = groups[1]
    ans = []
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                   f"WHERE Difficulty='{difficulty}' AND Id={id}")
    chart_data = cursor.fetchone()
    conn.close()
    if chart_data:
        total_basic = 1 * chart_data[0] + 2 * chart_data[1] + 3 * chart_data[2] + 5 * chart_data[4]
        total_basic += 1 * chart_data[3] if chart_data[3] else 0
        total_ex = chart_data[4]
        user_chart = [[int(groups[2]), int(groups[3]), int(groups[4])],
                      [int(groups[5]), int(groups[6]), int(groups[7])],
                      [int(groups[8]), int(groups[9]), int(groups[10])],
                      [int(groups[11]), int(groups[12]), int(groups[13])],
                      [int(groups[14]), int(groups[15]), int(groups[16]), int(groups[17])]]
        user_basic = 0
        # check
        for i, amount in enumerate(chart_data):
            if not amount:
                continue
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
    else:
        return "谱面不存在哟～", None
    if not ans:
        return "可能性がない......", None
    msg = f"Break Perfect 分为0.75/0.5额外分，并且都有5基础分。\n" \
          f"Break Great 分为4/3/2.5基础分，并且都有0.4额外分。"
    for case in ans:
        msg += f"\nP0.75:{case[0]}  P0.5:{case[1]}  Gr4:{case[2]}  Gr3:{case[3]}  Gr2.5:{case[4]}"
    return _check_combo(user_chart), str(image_to_base64(text_to_image(msg)), encoding="utf-8")


def select_chart(user_in: str):
    global difficulty_alias, chart_regex
    regex = "(看谱|查谱) " + difficulty_regex + "([0-9]+)\s?(.+)?"
    [_, difficulty, id, version] = re.match(regex, user_in.lower()).groups()
    if not difficulty or difficulty not in difficulty_alias:
        return "难度输入不对哦！", ""
    version = "舞萌DX 2021" if not version else version
    version = version.strip().replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(DISTINCT Version) FROM ChartDifficulty WHERE Version LIKE '%{version}%'")
    if cursor.fetchone()[0] != 1:
        return "这是什么大版本呀？", ""
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    cursor.execute(f"SELECT SI.Title,SI.ChartType,SI.BPM,CI.Id,CI.Difficulty,CI.Charter,CI.Tap,CI.Hold,CI.Slide,"
                   f"CI.Touch,CI.Break,CD.Level,CD.InnerLevel,CD.Version FROM SongInfo SI LEFT JOIN "
                   f"ChartInfo CI ON CI.Id=SI.Id LEFT JOIN ChartDifficulty CD ON CI.Difficulty=CD.Difficulty "
                   f"WHERE CI.Id={id} AND CI.Difficulty='{difficulty}' AND CD.Version LIKE '%{version}%'")
    res, img_path = cursor.fetchone(), ""
    conn.close()
    if not res:
        return "谱面不存在哟！检查下 ID 或者难度～", ""
    if res:
        msg = f"""
标题：{res[0]}
ID: {res[3]}
谱面类型：{res[1]}
BPM: {res[2]}
难度：{res[4]}
等级：{res[11]}
定数：{res[12]}
Tap: {res[6]}
Hold: {res[7]}
Slide: {res[8]}
"""
        if res[9]:
            msg += f"""Touch: {res[9]}
"""
        msg += f"""Break: {res[10]}
谱师：{res[5]}
定级版本：{res[13]}"""
        img = Image.open(BytesIO(id))
        return msg, str(image_to_base64(img), encoding="utf-8")
    else:
        return "谱面不存在哟！检查下 ID 或者难度～", ""


def random_chart(user_in: str):
    regex = r"我要大战(.+)"
    [keyword] = re.match(regex, user_in).groups()
    keywords = keyword.replace("'", "\\'")
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT CI.Id,CD.Difficulty FROM ChartInfo CI JOIN ChartDifficulty CD ON CI.Id=CD.Id "
                   f"AND CI.Difficulty=CD.Difficulty WHERE CI.Charter LIKE '%{keywords}%' AND CD.Version='舞萌DX 2021'")
    res = cursor.fetchall()
    conn.close()
    if res:
        id, difficulty = random.choice(res)
        return select_chart(f"看谱 {difficulty}{id}")
    else:
        return "", ""


# return: text, image (in BASE64 string)
async def get_achie_list(user_in: str, user_id: int):
    def _find_level_achi(start: int, end: int, qu: Queue):
        nonlocal data, ans
        for chart in data["verlist"][start:end]:
            if chart["level"] == level:
                ans.append(chart)
        qu.put(1)

    # [level, page, username]
    regex = r"(分数|达成率)列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?"
    [_, level, page, username] = re.match(regex, user_in.upper()).groups()
    page = int(page) if page else 1
    payload = {"username": username} if username else {"qq": user_id}
    payload["version"] = get_all_request_versions()
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data, None
    ans = []
    played = len(data["verlist"])
    qu, qu_count = Queue(), 0
    for i in range(cpu_thread_amount):
        Process(target=_find_level_achi, args=(int(played / cpu_thread_amount * i),
                                               int(played / cpu_thread_amount * (i + 1)),
                                               qu)).run()
    while qu_count != cpu_thread_amount:
        if qu.get():
            qu_count += 1
    total_pages = ceil(len(ans) / 25)
    if not ans:
        return "真的打过这个等级嘛？", None
    ans.sort(key=lambda x: x["achievements"], reverse=True)
    ans = ans[25 * (page - 1):min(25 * page, len(ans))]
    msg = f"你的等级{level}达成率列表第{page}/{total_pages}页如下："
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    for chart in ans:
        cursor.execute(f"SELECT InnerLevel FROM ChartDifficulty WHERE Id='{chart['id']}' AND "
                       f"Difficulty='{difficulty_alias[difficulty_short[chart['level_index']].lower()]}' AND "
                       f"Version='舞萌DX 2021'")
        [inner_level] = cursor.fetchone()
        difficulty = difficulty_short[chart["level_index"]]
        # XXX.XXXX FC+ DX Title
        msg += f"\n{chart['achievements']:8.4f}  {combo_upper[chart['fc']]:3}  {chart['type']}  " \
               f"{difficulty}{float(inner_level)}  {chart['title']}"
    conn.close()
    msg += f"\nCreated by LisaBot, maintained by Koto(RINkoTO)"
    return "", str(image_to_base64(text_to_image(msg)), encoding="utf-8")


async def get_level_process(user_in: str, user_id: int):
    regex = "^进度 ([0-9]+\+?) " + achie_ranks_regex + "?\s?" + combo_ranks_regex + "?\s?" \
            + sync_ranks_regex + "?\s?(.+)?"
    [level, achi_rank, combo, sync, username] = re.match(regex, user_in.upper()).groups()
    if not achi_rank and not combo and not sync:
        return "何が知りたい？"
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM ChartDifficulty WHERE Level='{level}' AND Version='舞萌DX 2021'")
    total, count = cursor.fetchone()[0], 0
    conn.close()
    if not total:
        return "本当にこのレベルが有りますか？"
    payload = {"username": username} if username else {"qq": user_id}
    payload["version"] = get_all_request_versions()
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    count = 0

    def _check_each(start: int, end: int, qu: Queue):
        nonlocal achi_rank, combo, count
        if achi_rank and (combo or sync):
            for chart in data["verlist"][start:end]:
                if chart["level"] == level and chart["achievements"] >= achie_ranks[achi_rank] and \
                        combo_ranks[chart["fc"]] <= combo_ranks[combo] and sync_ranks[chart["fs"]] <= sync_ranks[sync]:
                    count += 1
        elif achi_rank:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level and chart["achievements"] >= achie_ranks[achi_rank]:
                    count += 1
            combo = ""
        elif combo or sync:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level and combo_ranks[chart["fc"]] <= combo_ranks[combo] and \
                        sync_ranks[chart["fs"]] <= sync_ranks[sync]:
                    count += 1
            achi_rank = ""
        qu.put(1)

    qu, qu_count = Queue(), 0
    played = len(data["verlist"])
    for i in range(cpu_thread_amount):
        Process(target=_check_each, args=(int(played / cpu_thread_amount * i),
                                          int(played / cpu_thread_amount * (i + 1)), qu)).run()
    while qu_count != cpu_thread_amount:
        if qu.get():
            qu_count += 1
    msg = f"你的等级 {level} {achi_rank} {combo} {sync} 完成进度{count}/{total}\n"
    msg += f"まだ{total - count}残ります〜" if total != count else "できましたおめでとう！"
    return msg


async def get_plate_process(user_in: str, user_id: int) -> str:
    def _find_finished(start: int, end: int, plate: str, qu: Queue):
        nonlocal charts, finished_amount, unfinished_chart
        if plate_require[plate] in achie_ranks.keys():
            for chart in charts[start:end]:
                if (chart["id"] != 853 and ver == '舞') or (chart["id"] not in [70, 853] and chart["level_index"] != 4):
                    if chart["achievements"] >= achie_ranks[plate_require[plate]]:
                        finished_amount[chart["level_index"]] += 1
                    elif len(unfinished_chart) < 5:
                        unfinished_chart.append(chart)
        elif plate_require[plate] in combo_ranks.keys():
            for chart in charts[start:end]:
                if (chart["id"] != 853 and ver == '舞') or (chart["id"] not in [70, 853] and chart["level_index"] != 4):
                    if combo_ranks[combo_upper[chart["fc"]]] <= combo_ranks[plate_require[plate]]:
                        finished_amount[chart["level_index"]] += 1
                    elif len(unfinished_chart) < 5:
                        unfinished_chart.append(chart)
        elif plate_require[plate] in sync_ranks.keys():
            for chart in charts[start:end]:
                if (chart["id"] != 853 and ver == '舞') or (chart["id"] not in [70, 853] and chart["level_index"] != 4):
                    if sync_ranks[sync_upper[chart["fs"]]] <= sync_ranks[plate_require[plate]]:
                        finished_amount[chart["level_index"]] += 1
                    elif len(unfinished_chart) < 5:
                        unfinished_chart.append(chart)
        qu.put(1)

    regex = f"({'|'.join(version_aliases.keys())})?({'|'.join(plate_require.keys())})进度\s?(.+)?"
    # ver = 版本，plate = 牌子（含霸者）
    ver, plate, username = re.match(regex, user_in).groups()
    if ver == "真" and plate == "将":
        return "没有真将哦！"
    if plate in ["霸者", "覇者"]:
        ver = "舞"
    payload = {"version": version_aliases[ver][2]}
    if username:
        payload["username"] = username
    else:
        payload["qq"] = str(user_id)
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    charts = data["verlist"]
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    version_regex = "','".join(version_aliases[ver][1])
    # use ChinaVersion in Table SongInfo
    if ver == '舞':
        cursor.execute(f"SELECT COUNT(DISTINCT SI.Id),COUNT(*) FROM SongInfo SI JOIN ChartDifficulty CD ON SI.Id=CD.Id "
                       f"WHERE SI.ChinaVersion IN ('{version_regex}') AND CD.Version='舞萌DX 2021' AND SI.Id!=853")
    else:
        cursor.execute(f"SELECT COUNT(DISTINCT SI.Id),COUNT(*) FROM SongInfo SI JOIN ChartDifficulty CD ON SI.Id=CD.Id "
                       f"WHERE SI.ChinaVersion IN ('{version_regex}') AND CD.Version='舞萌DX 2021' "
                       f"AND CD.Difficulty!='Re:MASTER' AND SI.Id NOT IN (70,853)")
    song_amount, chart_amount = cursor.fetchone()
    conn.close()

    # find finished charts
    played, finished_amount, unfinished_chart = len(charts), [0, 0, 0, 0, 0], []
    qu, qu_count = Queue(), 0
    for i in range(cpu_thread_amount):
        Process(target=_find_finished, args=(int(played / cpu_thread_amount * i),
                                             int(played / cpu_thread_amount * (i + 1)), plate, qu)).run()
    while qu_count != cpu_thread_amount:
        if qu.get():
            qu_count += 1
    text = f"{plate}的要求是 {plate_require[plate]}\n" \
           f"你的{ver}{plate}完成情况如下：\n"
    if sum(finished_amount) == chart_amount:
        text += f"不剩！できました、おめでとう！"
    else:
        text += f"已完成{sum(finished_amount)}/{chart_amount}，剩余{chart_amount - sum(finished_amount)}\n" \
                f"各难度剩余情况如下：\n"
        for difficulty, amount in zip(["Basic", "Advanced", "Expert", "Master"], finished_amount):
            if amount == song_amount:
                continue
            text += f"{difficulty}  {song_amount - amount}/{song_amount}\n"
        if ver == '舞':
            text += f"Re:Master  {chart_amount - 4 * song_amount - finished_amount[4]}/" \
                    f"{chart_amount - 4 * song_amount}\n"
        if 0 < len(unfinished_chart) < 5:
            text += f"已游玩但未达成谱面如下：\n"
            for chart in unfinished_chart:
                text += f"{difficulty_short[chart['level_index']]}  {chart['id']}  {chart['title']}\n"
        text += f"拼机最快需要{ceil((chart_amount - sum(finished_amount)) / 4)}局"
        text += f"，单刷最快需要{ceil((chart_amount - sum(finished_amount)) / 3)}局\n" if plate != "舞舞" else "\n"
        text += "頑張ってね！"
    return text


def get_achi_line(user_in: str):
    regex = "(达成率|分数)线 " + difficulty_regex + "([0-9]+)\s?(0\+|100|101\-)?\s?(.+)?"
    _, difficulty, id, mode, version = re.match(regex, user_in.lower()).groups()
    version = "舞萌DX 2021" if not version else version
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(DISTINCT Version) FROM ChartDifficulty WHERE Version LIKE '%{version}%'")
    if cursor.fetchone()[0] != 1:
        return "这是什么大版本呀？", ""
    if not difficulty or difficulty not in difficulty_alias:
        return "难度输入不对哦！", ""
    difficulty = difficulty_alias[difficulty]
    mode = "101-" if not mode else mode
    cursor.execute(f"SELECT Tap,Hold,Slide,Touch,Break FROM ChartInfo "
                   f"WHERE Difficulty='{difficulty}' AND Id={id}")
    chart_data = cursor.fetchone()
    if not chart_data:
        return "谱面不存在哦！", ""
    conn.close()
    total_base, total_ex = 1 * chart_data[0] + 2 * chart_data[1] + 3 * chart_data[2] + 5 * chart_data[4] + \
                           (0 if not chart_data[3] else 1 * chart_data[3]), chart_data[4]
    note_score, judge_coef, ans = [1, 2, 3, 1], [1, 1, 0.8, 0.5, 0], []
    if mode == "101-":
        base_pic = Image.open("./material/achi_line_bg/101-reduce-lisa.png")
        for i, score in enumerate(note_score):
            ans.append([])
            if not chart_data[i]:
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
            if not chart_data[i]:
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
            if not chart_data[i]:
                continue
            for coef in judge_coef:
                ans[i].append(-((score - score * coef) / total_base * 100))
        ans.append([1 / total_ex, 0.75 / total_ex, 0.5 / total_ex, -1 / total_base * 100 + 0.4 / total_ex,
                    -2 / total_base * 100 + 0.4 / total_ex, -2.5 / total_base * 100 + 0.4 / total_ex,
                    -3 / total_base * 100 + 0.3 / total_ex, -5 / total_base * 100])
    cursor.execute(f"SELECT SI.Title,CD.InnerLevel FROM SongInfo SI LEFT JOIN ChartDifficulty CD "
                   f"ON SI.Id=CD.Id WHERE SI.Id={id} AND CD.Difficulty='{difficulty}' AND "
                   f"CD.Version LIKE '%{version}%'")
    try:
        title, inner_level = cursor.fetchone()
    except TypeError:
        return "谱面不存在哦～", ""
    base_drawer = ImageDraw.Draw(base_pic)
    cover_frame = Image.open(f"./material/difficulty_frame/UI_UPE_MusicJacket_Base_"
                             f"{difficulty_file[difficulty]}.png").resize((146, 133))
    base_pic.paste(cover_frame, (101, 73), mask=cover_frame.split()[3])
    cover_img = Image.open(BytesIO(fetch_song_cover(id))).resize((103, 103))
    base_pic.paste(cover_img, (123, 89), mask=cover_img.split()[3])
    title_font = ImageFont.truetype("./SourceHanSans_17.ttf", 36, encoding="utf-8")
    limit = lambda text: text if title_font.getsize(text)[0] <= 680 else limit(text[:-1])
    title = limit(title)
    base_drawer.text((264, 75), title, "#083060", font=title_font)
    info_font = ImageFont.truetype("./SourceHanSans_17.ttf", 22, encoding="utf-8")
    base_drawer.text((264, 135), f"{difficulty}  {inner_level}            ID: {id}            Notes: "
                                 f"{sum(chart_data) if chart_data[3] else sum(chart_data[0:3] + chart_data[-1:])}",
                     f"#083060", font=info_font)
    for x, note in zip((314, 470, 611, 770, 920), chart_data):
        base_drawer.text((x, 171), f"{note if note else '-'}", "#083060", font=info_font)
    for i, y in enumerate((337, 383, 428, 473)):
        if not chart_data[i]:
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
    great_font = ImageFont.truetype("./SourceHanSans_17.ttf", 23, encoding="utf-8")
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
    return str(image_to_base64(base_pic), encoding="utf-8"), ""


# return: text, image path
def get_ver_plates(user_in: str):
    regex = "^牌子(条件|列表)\s?(.+)?"
    _, ver = re.match(regex, user_in).groups()
    if ver not in ver_file.keys():
        return f"使用方法是：牌子条件 [版本简称]\n版本简称包含如下：{'、'.join(ver_file.keys())}", ""
    if os.path.exists(f"./material/plate_requirement/Lisa/{ver_file[ver]}-lisa.png"):
        return "", f"file://{os.getcwd()}/material/plate_requirement/Lisa/{ver_file[ver]}-lisa.png"
    else:
        return "该版本牌子还没有上线～", ""


def cal_single_rating_line(user_in: str) -> str:
    def _cal_single_rating(i: int, achi: float, inner_level: float) -> int:
        achi_rank_coef_dict = {"SSS+": 14, "SSS": 13.5, "SS+": 13.2, "SS": 13.0, "S+": 12.7, "S": 12.5,
                               "AAA": 10.5, "AA": 9.5, "A": 8.5, "BBB": 7.5, "BB": 7.0, "B": 6.0,
                               "C": 5.0, "D": 0}
        achi_rank_coef_list = tuple(achi_rank_coef_dict.keys())
        achi = 100.5 if achi > 100.5 else achi
        return int(achi / 100 * achi_rank_coef_dict[achi_rank_coef_list[i]] * float(inner_level))

    def _rating_to_achievement(i: int, single_rating: int, inner_level: float) -> Any:
        achi_rank_coef_dict = {"SSS+": 14.0, "SSS": 13.5, "SS+": 13.2, "SS": 13.0, "S+": 12.7, "S": 12.5,
                               "AAA": 10.5, "AA": 9.5, "A": 8.5, "BBB": 7.5, "BB": 7.0, "B": 6.0, "C": 5.0}
        achi_rank_coef_list = tuple(achi_rank_coef_dict.keys())
        achie_ranks_list = tuple(achie_ranks.keys())
        achi_trial = round(single_rating / achi_rank_coef_dict[achi_rank_coef_list[i]] / inner_level * 100, 4)
        if achie_ranks[achie_ranks_list[i - 1]] > achi_trial >= achie_ranks[achie_ranks_list[i]]:
            return achi_trial
        else:
            return None

    regex = "^单曲(rating|ra) ([0-9]+\.[0-9])"
    _, inner_level = re.match(regex, user_in.lower()).groups()
    inner_level = float(inner_level)
    ans = [(100.5, _cal_single_rating(0, 100.5, inner_level))]
    for i, achi in enumerate(tuple(achie_ranks.values())[1:6]):
        sin_ra = _cal_single_rating(i + 1, achi, inner_level)
        for sin_ra_trial in range(sin_ra + 1, sin_ra + 3):
            achi_trial = _rating_to_achievement(i + 1, sin_ra_trial, inner_level)
            if achi_trial:
                ans.append((achi_trial, sin_ra_trial))
        ans.append((achi, sin_ra))
    return f"定数{inner_level}的单曲 rating\n" + "\n".join([f"{ra}: {achi:03.4f}%" for achi, ra in ans])
