import re
import random
import os
from tools.get_data_func import *
from tools.image import *
from tools.shared_var import *
from _thread import start_new_thread, allocate_lock
from math import ceil

random.seed(2508)


def check_combo(user_chart):
    state = None
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
    conn = database_pool.connection()
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
        return f"{round(max_achie, 4)}% ~ {round(min_achie, 4)}%\n" \
               f"结果可能存在略微偏差\n" + check_combo(user_chart)
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
    conn = database_pool.connection()
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
    return check_combo(user_chart), text_to_image(msg)


def select_chart(user_in: str):
    global difficulty_alias, chart_regex
    regex = "(看谱|查谱) " + difficulty_regex + "([0-9]+)\s?(.+)?"
    [_, difficulty, id, version] = re.match(regex, user_in.lower()).groups()
    if difficulty and difficulty not in difficulty_alias:
        return "难度输入不对哦！", ""
    version = "舞萌DX 2021" if not version else version
    conn = database_pool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(DISTINCT Version) FROM ChartDifficulty WHERE Version LIKE '%{version}%'")
    if cursor.fetchone()[0] != 1:
        return "这是什么大版本呀？", ""
    difficulty = difficulty_alias[difficulty] if difficulty else '%'
    cursor.execute(f"SELECT SI.Title,SI.Cover,SI.ImageExt,CI.*,CD.Level,CD.InnerLevel,CD.Version FROM ChartInfo CI "
                   f"LEFT JOIN ChartDifficulty CD ON CI.Id=CD.Id AND CI.Difficulty=CD.Difficulty "
                   f"RIGHT JOIN SongInfo SI ON CI.Id=SI.Id "
                   f"WHERE CI.Id={id} AND CI.Difficulty='{difficulty}' AND CD.Version LIKE '%{version}%'")
    res, img_path = cursor.fetchone(), ""
    conn.close()
    if not res:
        return "谱面不存在哟！检查下 ID 或者难度～", ""
    if res:
        msg = f"""
标题：{res[0]}
ID: {res[3]}
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
        with open("./cache/chart_cover" + res[2], "wb") as cover:
            cover.write(res[1])
        img_path = f"file://{os.getcwd()}/cache/chart_cover" + res[2]
    else:
        msg = "谱面不存在哟！检查下 ID 或者难度～"
    return msg, img_path


def random_chart(user_in: str):
    regex = r"我要大战(.+)"
    [keyword] = re.match(regex, user_in).groups()
    keywords = keyword.replace("'", "\\'")
    conn = database_pool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT CI.Id,CD.Difficulty FROM ChartInfo CI JOIN ChartDifficulty CD "
                   f"ON CI.Id=CD.Id AND CI.Difficulty=CD.Difficulty "
                   f"WHERE CI.Charter LIKE '%{keywords}%'")
    res = cursor.fetchall()
    conn.close()
    if res:
        [[id, difficulty]] = random.sample(res, 1)
        return select_chart(f"看谱 {difficulty}{id}")
    else:
        return "", ""


async def get_achie_list(user_in: str, user_id: int):
    def _find_level_achi(start: int, end: int, lock):
        nonlocal data, ans
        for chart in data["verlist"][start:end]:
            if chart["level"] == level:
                ans.append(chart)
        lock.release()

    # [level, page, username]
    regex = r"(分数|达成率)列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?"
    [_, level, page, username] = re.match(regex, user_in.upper()).groups()
    page = int(page) if page else 1
    payload = {"username": username} if username else {"qq": user_id}
    payload["version"] = list(set(version for version in version_alias.values()))
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    ans, locks_list = [], []
    played = len(data["verlist"])
    for i in range(4):
        lock = allocate_lock()
        lock.acquire()
        locks_list.append(lock)
    # for i in range(4):
        start_new_thread(_find_level_achi, (int(played / 4 * i), int(played / 4 * (i + 1)), locks_list[i]))
    while any(lock.locked() for lock in locks_list):
        pass
    total_pages = ceil(len(ans) / 25)
    if not ans:
        return "真的打过这个等级嘛？"
    ans.sort(key=lambda x: x["achievements"], reverse=True)
    ans = ans[25 * (page - 1):min(25 * page, len(ans))]
    msg = f"你的等级{level}达成率列表第{page}/{total_pages}页如下："
    conn = database_pool.connection()
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
    msg += f"\nCreated by LisaBot, maintained by Koto"
    return image_to_base64(text_to_image(msg))


async def get_level_process(user_in: str, user_id: int):
    regex = "进度 ([0-9]+\+?)\s?" + combo_ranks_regex + "?\s?" + achie_ranks_regex + "?\s?(.+)?"
    [level, combo, rank, username] = re.match(regex, user_in.upper()).groups()
    if not rank and not combo:
        return "何が知ったい？"
    conn = database_pool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM ChartDifficulty WHERE Level='{level}' AND Version='舞萌DX 2021'")
    total, count = cursor.fetchone()[0], 0
    conn.close()
    if not total:
        return "本当にこのレベルが有りますか？"
    payload = {"username": username} if username else {"qq": user_id}
    payload["version"] = list(set(version for version in version_alias.values()))
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    count = 0
    locks_list = []

    def _check_each(start: int, end: int, lock):
        nonlocal rank, combo, count
        if rank and combo:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level and chart["achievements"] >= achie_ranks[rank] \
                        and combo_ranks[chart["fc"]] <= combo_ranks[combo]:
                    count += 1
        elif rank:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level and chart["achievements"] >= achie_ranks[rank]:
                    count += 1
            combo = ""
        elif combo:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level and combo_ranks[chart["fc"]] <= combo_ranks[combo]:
                    count += 1
            rank = ""
        lock.release()

    played = len(data["verlist"])
    for i in range(4):
        lock = allocate_lock()
        lock.acquire()
        locks_list.append(lock)
    # for i in range(4):
        start_new_thread(_check_each, (int(played / 4 * i), int(played / 4 * (i + 1)), locks_list[i]))
    while any(lock.locked() for lock in locks_list):
        pass
    msg = f"你的等级 {level} {rank} {combo} 完成进度{count}/{total}\n"
    msg += f"まだ{total - count}残ります〜" if total != count else "できましたおめでとう！"
    return msg


async def get_plate_process(user_in: str, user_id: int) -> str:
    def _find_finished(start: int, end: int, lock, plate: str):
        nonlocal charts, finished
        if plate_require[plate] in achie_ranks.keys():
            for chart in charts[start:end]:
                if chart["achievements"] >= achie_ranks[plate_require[plate]]:
                    finished[chart["level_index"]] += 1
        elif plate_require[plate] in combo_ranks.keys():
            for chart in charts[start:end]:
                if combo_ranks[combo_upper[chart["fc"]]] <= combo_ranks[plate_require[plate]]:
                    finished[chart["level_index"]] += 1
        elif plate_require[plate] in sync_ranks.keys():
            for chart in charts[start:end]:
                if sync_ranks[sync_upper[chart["fs"]]] <= sync_ranks[plate_require[plate]]:
                    finished[chart["level_index"]] += 1
        lock.release()

    def _pop_unneeded_charts(charts, lock):
        nonlocal plate, ver, charts_part
        i = 0
        while i < len(charts):
            if charts[i]["id"] == 70 or charts[i]["id"] == 853:
                charts.pop(i)
            elif plate != "霸者" and ver != '舞' and charts[i]["level_index"] == 4:
                charts.pop(i)
            else:
                i += 1
        charts_part += charts
        lock.release()

    regex = f"({'|'.join(version_alias.keys())})?({'|'.join(plate_require.keys())})进度\s?(.+)?"
    # ver = 版本，plate = 牌子/霸者
    ver, plate, username = re.match(regex, user_in).groups()
    ver = "真" if ver == "初" else ("熊" if ver in ['華', '华'] else ver)
    if ver == "真" and plate == "将":
        return "没有真将哦！"
    if plate == "霸者" or ver == "舞":
        payload = {"version": list(set(version for version in version_alias.values()))}
        i = 0
        while i < len(payload["version"]):
            if re.search("でらっくす", payload["version"][i]):
                payload["version"].pop(i)
            else:
                i += 1
    elif ver == "真":
        payload = {"version": [version_alias["初"], version_alias["真"]]}
    else:
        payload = {"version": [version_alias[ver]]}
    if username:
        payload["username"] = username
    else:
        payload["qq"] = str(user_id)
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    charts = data["verlist"]

    conn = database_pool.connection()
    cursor = conn.cursor()
    # 真 = maimai + maimai PLUS
    if ver == "真":
        cursor.execute(f"SELECT COUNT(DISTINCT SI.Id) FROM SongInfo SI JOIN ChartDifficulty CD ON SI.Id=CD.Id "
                       f"WHERE SI.Version IN ('{version_alias['初']}','{version_alias['真']}') AND "
                       f"CD.Version='舞萌DX 2021' AND CD.Difficulty!='Re:MASTER'")
        [song_amount] = cursor.fetchone()
        # ジングルベル
        song_amount -= 1
        chart_amount = int(song_amount * 4) - 4
    elif ver == "熊":
        song_amount, chart_amount = 95, 380
    # GreeN to FiNALE, no Re:M
    elif plate != "霸者" and ver != "舞":
        cursor.execute(f"SELECT COUNT(DISTINCT SI.Id) FROM SongInfo SI JOIN ChartDifficulty CD ON SI.Id=CD.Id WHERE "
                       f"SI.Version='{version_alias[ver].replace('でらっくす', 'DX') if ver != '雪' else 'maimai MiLK PLUS'}' "
                       f"AND CD.Version='舞萌DX 2021' AND CD.Difficulty!='Re:MASTER'")
        [song_amount] = cursor.fetchone()
        # 前前前世
        song_amount -= 1 if ver in ['菫', '堇'] else 0
        chart_amount = int(song_amount * 4)
        chart_amount -= 4 if ver == '菫' or ver == '堇' else 0
    # 舞XX或霸者
    elif plate == "霸者" or ver == '舞':
        cursor.execute(f"SELECT COUNT(DISTINCT SI.Id) FROM SongInfo SI JOIN ChartDifficulty CD ON SI.Id=CD.Id "
                       f"WHERE SI.ChartType='SD' AND CD.Version='舞萌DX 2021'")
        [song_amount] = cursor.fetchone()
        song_amount -= 2
        cursor.execute(f"SELECT COUNT(*) FROM SongInfo SI JOIN ChartDifficulty CD ON SI.Id=CD.Id "
                       f"WHERE SI.ChartType='SD' AND CD.Version='舞萌DX 2021'")
        [chart_amount] = cursor.fetchone()
        chart_amount -= 9
    conn.close()

    # pop charts not required finished
    played = len(charts)
    locks_list, charts_part = [], []
    for i in range(4):
        lock = allocate_lock()
        lock.acquire()
        locks_list.append(lock)
    # for i in range(4):
        start_new_thread(_pop_unneeded_charts, (charts[int(played / 4 * i):int(played / 4 * (i + 1))], locks_list[i]))
    while any(lock.locked() for lock in locks_list):
        pass
    charts = charts_part

    # find finished charts
    played, finished = len(charts), [0, 0, 0, 0, 0]
    for i in range(4):
        locks_list[i].acquire()
    # for i in range(4):
        start_new_thread(_find_finished, (int(played / 4 * i), int(played / 4 * (i + 1)), locks_list[i], plate))
    while any(lock.locked() for lock in locks_list):
        pass

    msg = f"你的{ver if ver else ''}{plate}总完成进度{sum(finished)}/{chart_amount}\n" \
          f"{plate}的达成要求是 {plate_require[plate]}\n" \
          f"未完成情况如下："
    for i, difficulty in enumerate(["Basic", "Advanced", "Expert", "Master"]):
        msg += f"\n{difficulty}  {song_amount - finished[i]}/{song_amount}"
    if plate == "霸者" or ver == '舞':
        msg += f"\nRe:MASTER  {chart_amount - 4 * song_amount - finished[4]}/{chart_amount - 4 * song_amount}"
    msg += f"\n剩余{chart_amount - sum(finished)}张谱" \
           f"\n单刷最快需要{int(ceil((chart_amount - sum(finished)) / 3))}局捏！"
    return msg