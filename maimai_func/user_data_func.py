import json
import re
import random
import os
from abc import abstractmethod
from typing import Any

import numpy as np
import requests

from models.mai_models import *
from models.player_models import *
from tools.get_player_data import *
from tools.image import *
from tools.shared_var import *
from math import ceil
from multiprocessing import Process, Queue

random.seed(2508)
translate_dict = {'fs': 'FS', 'fsp': 'FSp', 'fc': 'FC', 'fcp': 'FCp',
                  'fsd': 'FSD', 'fsdp': 'FSDp', 'ap': 'AP', 'app': 'APp', '': ''}
title_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 20, encoding="utf-8")
achi_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 24, encoding="utf-8")
level_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 14, encoding="utf-8")
sin_rating_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 18, encoding="utf-8")


# return: text, image (in BASE64 string)
async def get_level_list(user_in: str, user_id: int):
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
    payload["version"] = all_versions
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data, None
    ans = []
    played = len(data["verlist"])
    qu, qu_count = Queue(), 0
    for i in range(cpu_thread_amount):
        Process(target=_find_level_achi,
                args=(int(played / cpu_thread_amount * i), int(played / cpu_thread_amount * (i + 1)), qu)).run()
    while qu_count != cpu_thread_amount:
        if qu.get():
            qu_count += 1
    total_pages = ceil(len(ans) / 25)
    if not ans:
        return "真的打过这个等级嘛？", None
    ans.sort(key=lambda x: x["achievements"], reverse=True)
    ans = ans[25 * (page - 1):min(25 * page, len(ans))]
    msg = f"你的等级{level}达成率列表第{page}/{total_pages}页如下："
    for record in ans:
        difficulty = difficulty_short[record["level_index"]]
        chart = ChartDifficulty. \
            select(ChartDifficulty.inner_level). \
            join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
            where((SongInfo.title == record["title"]) & (SongInfo.chart_type == record["type"]) &
                  (ChartDifficulty.difficulty == difficulty_alias[difficulty.lower()]) &
                  (ChartDifficulty.version == "舞萌DX2022")). \
            get()
        # XXX.XXXX FC+ DX Title
        msg += f"\n{record['achievements']:8.4f}  {combo_upper[record['fc']]:3}  {record['type']}  " \
               f"{difficulty}{chart.inner_level}  {record['title']}"
    msg += f"\nCreated by LisaBot, maintained by Koto(RINkoTO)"
    return "", str(image_to_base64(text_to_image(msg)), encoding="utf-8")


async def get_level_process(user_in: str, user_id: int):
    regex = "^进度 ([0-9]+\+?) " + achie_ranks_regex + "?\s?" + combo_ranks_regex + "?\s?" \
            + sync_ranks_regex + "?\s?(.+)?"
    [level, achi_rank, combo, sync, username] = re.match(regex, user_in.upper()).groups()
    if not achi_rank and not combo and not sync:
        return "何が知りたい？"
    count = 0
    amount = ChartDifficulty. \
        select(fn.COUNT(ChartDifficulty.id).alias('count')). \
        where((ChartDifficulty.level == level) & (ChartDifficulty.version == '舞萌DX2022')). \
        get()
    if not amount.count:
        return "本当にこのレベルが有りますか？"
    payload = {"username": username} if username else {"qq": user_id}
    payload["version"] = all_versions
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    count = 0

    def _check_each(start: int, end: int, qu: Queue):
        nonlocal achi_rank, combo, count, unfinished_charts
        if achi_rank and (combo or sync):
            for chart in data["verlist"][start:end]:
                if chart["level"] == level:
                    if chart["achievements"] >= achie_ranks[achi_rank] and \
                            combo_ranks[chart["fc"]] <= combo_ranks[combo] and \
                            sync_ranks[chart["fs"]] <= sync_ranks[sync]:
                        count += 1
                    else:
                        unfinished_charts.append(chart)
        elif achi_rank:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level:
                    if chart["achievements"] >= achie_ranks[achi_rank]:
                        count += 1
                    else:
                        unfinished_charts.append(chart)
            combo = ""
        elif combo or sync:
            for chart in data["verlist"][start:end]:
                if chart["level"] == level:
                    if combo_ranks[chart["fc"]] <= combo_ranks[combo] and \
                            sync_ranks[chart["fs"]] <= sync_ranks[sync]:
                        count += 1
                    else:
                        unfinished_charts.append(chart)
            achi_rank = ""
        qu.put(1)

    qu, qu_count = Queue(), 0
    played, unfinished_charts = len(data["verlist"]), []
    for i in range(cpu_thread_amount):
        Process(target=_check_each, args=(int(played / cpu_thread_amount * i),
                                          int(played / cpu_thread_amount * (i + 1)), qu)).run()
    while qu_count != cpu_thread_amount:
        if qu.get():
            qu_count += 1
    text = f"你的等级 {level} {achi_rank} {combo} {sync} 完成进度{count}/{amount.count}\n"
    text += f"まだ{amount.count - count}残ります〜" if amount.count != count else "できましたおめでとう！"
    if 0 < len(unfinished_charts) < 5:
        text += f"\n已游玩但未达成谱面如下：\n"
        for chart in unfinished_charts:
            text += f"{difficulty_short[chart['level_index']]}  {chart['id']}  {chart['title']}\n"
    return text


async def get_plate_process(user_in: str, user_id: int) -> Optional[str]:
    def _find_finished(start: int, end: int, plate: str, qu: Queue):
        nonlocal charts, finished_amount, unfinished_charts
        if plate_require[plate] in achie_ranks.keys():
            for chart in charts[start:end]:
                if (chart["id"] != 853 and ver == '舞') or (chart["id"] not in [70, 853] and chart["level_index"] != 4):
                    if chart["achievements"] >= achie_ranks[plate_require[plate]]:
                        finished_amount[chart["level_index"]] += 1
                    elif len(unfinished_charts) < 5:
                        unfinished_charts.append(chart)
        elif plate_require[plate] in combo_ranks.keys():
            for chart in charts[start:end]:
                if (chart["id"] != 853 and ver == '舞') or (chart["id"] not in [70, 853] and chart["level_index"] != 4):
                    if combo_ranks[combo_upper[chart["fc"]]] <= combo_ranks[plate_require[plate]]:
                        finished_amount[chart["level_index"]] += 1
                    elif len(unfinished_charts) < 5:
                        unfinished_charts.append(chart)
        elif plate_require[plate] in sync_ranks.keys():
            for chart in charts[start:end]:
                if (chart["id"] != 853 and ver == '舞') or (chart["id"] not in [70, 853] and chart["level_index"] != 4):
                    if sync_ranks[combo_sync_upper[chart["fs"]]] <= sync_ranks[plate_require[plate]]:
                        finished_amount[chart["level_index"]] += 1
                    elif len(unfinished_charts) < 5:
                        unfinished_charts.append(chart)
        qu.put(1)

    def _translate_to_ja(source: str):
        ja = {"晓": "暁", "樱": "櫻", "堇": "菫", "辉": "輝", "霸": "覇", "华": "華", "极": "極"}
        for char in source:
            if char in ja:
                source = source.replace(char, ja[char])
        return source

    user_in = _translate_to_ja(user_in)
    regex = f"({'|'.join(version_alias.keys())})?({'|'.join(plate_require.keys())})?进度\s?(.+)?"
    # ver = 版本，plate = 牌子（含霸者）
    try:
        ver, requirement, username = re.match(regex, user_in).groups()
    except AttributeError:
        return None
    if ver == "真" and requirement == "将":
        return "没有真将哦！"
    if requirement == "覇者":
        ver = "舞"
    payload = {"version": version_alias[ver][2]}
    if username:
        payload["username"] = username
    else:
        payload["qq"] = str(user_id)
    data = await get_player_data(payload, "plate")
    if isinstance(data, str):
        return data
    charts = data["verlist"]
    # use ChinaVersion in Table SongInfo
    total_amount = ChartInfo. \
        select(fn.COUNT(ChartInfo.id.distinct()).alias('song_amount'), fn.COUNT(ChartInfo.id).alias('chart_amount')). \
        join(ChartDifficulty, on=(ChartInfo.id == ChartDifficulty.id) &
                                 (ChartInfo.difficulty == ChartDifficulty.difficulty)). \
        where((ChartDifficulty.version == '舞萌DX2022') & ChartInfo.plate_mask.bin_and(version_alias[ver][3])). \
        get()

    # find finished charts
    played, finished_amount, unfinished_charts = len(charts), [0, 0, 0, 0, 0], []
    qu, qu_count = Queue(), 0
    for i in range(cpu_thread_amount):
        Process(target=_find_finished, args=(int(played / cpu_thread_amount * i),
                                             int(played / cpu_thread_amount * (i + 1)), requirement, qu)).run()
    while qu_count != cpu_thread_amount:
        if qu.get():
            qu_count += 1
    text = f"{requirement}的要求是 {plate_require[requirement]}\n" \
           f"你的{ver}{requirement}完成情况如下：\n"
    if sum(finished_amount) == total_amount.chart_amount:
        text += f"不剩！できました、おめでとう！"
    else:
        text += f"已完成{sum(finished_amount)}/{total_amount.chart_amount}，" \
                f"剩余{total_amount.chart_amount - sum(finished_amount)}\n" \
                f"各难度剩余情况如下：\n"
        for difficulty, amount in zip(["Basic", "Advanced", "Expert", "Master"], finished_amount):
            if amount == total_amount.song_amount:
                continue
            text += f"{difficulty}  {total_amount.song_amount - amount}/{total_amount.song_amount}\n"
        if ver == '舞':
            text += f"Re:Master  {total_amount.chart_amount - 4 * total_amount.song_amount - finished_amount[4]}/" \
                    f"{total_amount.chart_amount - 4 * total_amount.song_amount}\n"
        if 0 < len(unfinished_charts) < 5:
            text += f"已游玩但未达成谱面如下：\n"
            for chart in unfinished_charts:
                text += f"{difficulty_short[chart['level_index']]}  {chart['id']}  {chart['title']}\n"
        text += f"拼机最快需要{ceil((total_amount.chart_amount - sum(finished_amount)) / 4)}局"
        text += f"，单刷最快需要{ceil((total_amount.chart_amount - sum(finished_amount)) / 3)}局\n" \
            if requirement != "舞舞" else "\n"
        text += "頑張ってね！"
    return text


def get_best_list(user_in: str, qq_id: int):
    _, mode, username = re.match("^(b|B)(4|5)0\s?(.+)?", user_in).groups()
    mode = "B40" if mode == "4" else "B50"
    best_list = Best40List(username, qq_id) if mode == "B40" else Best50List(username, qq_id)
    if best_list.get_from_home(mode):
        best_list.specific_frame(mode)
        text = None
    else:
        if best_list.get_data_from_third():
            text = "您正在使用第三方数据源"
            best_list.translate_from_third()
            best_list.specific_frame(mode)
        else:
            return None, "真的有这位玩家嘛？或者是没有绑定 QQ 号？"

    best_list.draw_pic()
    img = str(image_to_base64(best_list.get_pic()), encoding="utf-8")
    return img, text


def get_song_best():
    pass


class BestList:
    text_message: str
    error: str
    payload: dict
    best_list_response: dict
    username: str
    qq_id: int
    frame_no: str
    bg_img: Image.Image
    old_new_gap: int
    x_gap: int
    y_gap: int
    x_df: int
    y_df: int
    x_cover: int
    y_cover: int
    x_csr: int
    y_csr: int
    x_ct: int
    y_ct: int
    x_ar: int
    y_ar: int
    x_achi: int
    y_achi: int
    x_title: int
    y_title: int
    x_level: int
    y_level: int
    x_sin_rating: int
    y_sin_rating: int
    mode: str

    def __init__(self, username: str, qq_id: int):
        self.payload = {"version": all_versions}
        self.username, self.qq_id = username, qq_id

    def translate_from_third(self):
        def calculate_rank_no():
            rank_no_dict = {0: 0, 250: 1, 500: 2, 750: 3, 1000: 4, 1200: 5, 1400: 6, 1500: 7, 1600: 8, 1700: 9,
                            1800: 10, 1850: 11, 1900: 12, 1950: 13, 2000: 14}
            self.best_list_response["rank_no"] = rank_no_dict[self.best_list_response["rank_rating"]] \
                if self.best_list_response["rank_rating"] in rank_no_dict \
                else int(14 + (self.best_list_response["rank_rating"] - 2000) / 10)

        self.best_list_response["rank_rating"] = self.best_list_response["additional_rating"]
        self.best_list_response["records_old"] = self.best_list_response["charts"]["sd"]
        self.best_list_response["records_new"] = self.best_list_response["charts"]["dx"]
        calculate_rank_no()
        for chart in self.best_list_response["records_old"]:
            chart["inner_level"] = chart["ds"]
            chart["single_rating"] = chart["ra"]
            chart["achi_rank"] = chart["rate"].upper().replace("P", "p")
            chart["difficulty"] = chart["level_label"]
            chart["id"] = chart["song_id"]
            chart["chart_type"] = chart["type"]
            chart["dx_score"] = chart["dxScore"]
            chart["combo"] = translate_dict[chart["fc"]]
            chart["sync"] = translate_dict[chart["fs"]]
        for chart in self.best_list_response["records_new"]:
            chart["inner_level"] = chart["ds"]
            chart["single_rating"] = chart["ra"]
            chart["achi_rank"] = chart["rate"].upper().replace("P", "p")
            chart["difficulty"] = chart["level_label"]
            chart["id"] = chart["song_id"]
            chart["chart_type"] = chart["type"]
            chart["dx_score"] = chart["dxScore"]
            chart["combo"] = translate_dict[chart["fc"]]
            chart["sync"] = translate_dict[chart["fs"]]
        if self.best_list_response['plate']:
            groups = re.match(f"({'|'.join(ver for ver in ver_num_dict.keys())})"
                              f"({'|'.join(plate for plate in plate_num_dict.keys())})?",
                              self.best_list_response['plate']).groups()
            plate_num = ver_num_dict[groups[0]] + plate_num_dict[groups[1]] if groups[1] else ver_num_dict[
                groups[0]]
            plate_num += 1 if groups[0] == "真" and groups[1] == "極" else 0
            self.best_list_response['plate_id'] = f"{plate_num:06d}"
        else:
            self.best_list_response['plate_id'] = None

    def get_data_from_third(self) -> bool:
        if self.username:
            self.payload["username"] = self.username
        elif self.qq_id:
            self.payload["qq"] = str(self.qq_id)
        else:
            self.error = "QQ 号和用户名都获取不到，怎么回事呢？"
        resp = requests.post('https://www.diving-fish.com/api/maimaidxprober/query/player',
                             proxies={'http': None, 'https': None}, json=self.payload)
        if resp.status_code == 400:
            self.error = "真的有这位玩家嘛？或者是没有绑定 QQ 号？"
        elif resp.status_code == 403:
            self.error = '这位好像不给获取信息捏。'
        elif resp.status_code == 200:
            self.best_list_response = resp.json()
            return True
        else:
            self.error = '发生了错误，找找机修看看吧'
        return False

    def get_from_home(self, mode: str) -> bool:
        request_data = {"username": self.username, "qq_id": None} if self.username \
            else {'qq_id': self.qq_id, "username": None}
        request_data['mode'] = mode
        try:
            resp = requests.get("http://154.86.19.207:8000/player_query/best_records",
                                proxies={'http': None, 'https': None}, data=json.dumps(request_data))
            if resp.status_code != 200:
                self.error = resp.text
                return False
            else:
                self.best_list_response = resp.json()
            return True
        except ConnectionError:
            return False

    def specific_frame(self, mode):
        if self.best_list_response['dx_rating'] < 1000:
            self.frame_no = "01"
        elif self.best_list_response['dx_rating'] < 2000:
            self.frame_no = "02"
        elif self.best_list_response['dx_rating'] < (3000 if mode == "B40" else 4000):
            self.frame_no = "03"
        elif self.best_list_response['dx_rating'] < (4000 if mode == "B40" else 7000):
            self.frame_no = "04"
        elif self.best_list_response['dx_rating'] < (5000 if mode == "B40" else 10000):
            self.frame_no = "05"
        elif self.best_list_response['dx_rating'] < (6000 if mode == "B40" else 12000):
            self.frame_no = "06"
        elif self.best_list_response['dx_rating'] < (7000 if mode == "B40" else 13000):
            self.frame_no = "07"
        elif self.best_list_response['dx_rating'] < (8000 if mode == "B40" else 14000):
            self.frame_no = "08"
        elif self.best_list_response['dx_rating'] < 8500 and mode == "B40":
            self.frame_no = "09"
        elif self.best_list_response['dx_rating'] < 14500 and mode == "B50":
            self.frame_no = "09"
        elif self.best_list_response['dx_rating'] < 15000 and mode == "B50":
            self.frame_no = "10"
        else:
            self.frame_no = "11"

    def draw_pic(self):
        bg_drawer = ImageDraw.Draw(self.bg_img)

        # fetch cover from database, return cover path
        def _draw_cover(id: int, x: int, y: int):
            cover_img = Image.open(BytesIO(fetch_song_cover(id))).resize((80, 80))
            self.bg_img.paste(cover_img, (x, y))

        # frame outside song cover
        def _draw_difficulty_frame(difficulty: str, x: int, y: int):
            chart_frame_img = Image.open(f"./material/difficulty_frame/UI_UPE_MusicJacket_Base_"
                                         f"{difficulty_file[difficulty]}.png").resize((112, 102))
            self.bg_img.paste(chart_frame_img, (x, y), mask=chart_frame_img.split()[3])

        # AP/FC, FS/FSD
        def _draw_combo_sync_rank(combo_rank: str, sync_rank: str, x: int, y: int):
            if combo_rank:
                combo_img = Image.open(f"./material/rate_icon/UI_MSS_MBase_Icon_{combo_rank}.png").resize((28, 28))
                self.bg_img.paste(combo_img, (x, y), mask=combo_img.split()[3])
            if sync_rank:
                sync_img = Image.open(f"./material/rate_icon/UI_MSS_MBase_Icon_{sync_rank}.png").resize((28, 28))
                self.bg_img.paste(sync_img, (x + 24, y), mask=sync_img.split()[3])

        # 谱面类型
        def _draw_chart_type(chart_type: str, x: int, y: int):
            chart_type_img = Image.open("./material/chart_type/UI_TST_Infoicon_DeluxeMode.png").resize((50, 16)) \
                if chart_type == "DX" else \
                Image.open("./material/chart_type/UI_TST_Infoicon_StandardMode.png").resize((50, 16))
            self.bg_img.paste(chart_type_img, (x, y), mask=chart_type_img.split()[3])

        # 评级
        def _draw_achi_rank(achi_rank: str, x: int, y: int):
            rate_img = Image.open(f"./material/achieve_rank/UI_TTR_Rank_{achi_rank}.png").resize((64, 30))
            self.bg_img.paste(rate_img, (x, y), mask=rate_img.split()[3])

        # 曲名标题，限长226
        def _draw_title(title: str, x: int, y: int):
            limit = lambda text: text if title_font.getsize(text)[0] <= 226 else limit(text[:-1])
            title = limit(title)
            bg_drawer.text((x, y), title, "white", font=title_font)

        # 达成率
        def _draw_achi(achievements: float, x: int, y: int):
            bg_drawer.text((x, y), f"{achievements:.4f}%", "white", achi_font)

        # 定数
        def _draw_inner_level(inner_level: float, x: int, y: int):
            bg_drawer.text((x - level_font.getsize(f"{inner_level} ▶")[0], y), f"{inner_level} ▶", "black", level_font)

        # 单曲 rating
        def _draw_single_rating(single_rating: int, x: int, y: int):
            bg_drawer.text((x, y), f"{single_rating}", "black", sin_rating_font)

        def _draw_old_list(queue: Queue):
            i = 0
            for y in range(7):
                if i >= len(self.best_list_response["records_old"]):
                    break
                for x in range(5):
                    if i >= len(self.best_list_response["records_old"]):
                        break
                    chart = self.best_list_response["records_old"][i]
                    _draw_difficulty_frame(chart["difficulty"], self.x_df + x * self.x_gap, self.y_df + y * self.y_gap)
                    _draw_cover(chart["id"], self.x_cover + x * self.x_gap, self.y_cover + y * self.y_gap)
                    _draw_combo_sync_rank(chart["combo"], chart["sync"], self.x_csr + x * self.x_gap,
                                          self.y_csr + y * self.y_gap)
                    _draw_chart_type(chart["chart_type"], self.x_ct + x * self.x_gap, self.y_ct + y * self.y_gap)
                    _draw_achi_rank(chart["achi_rank"], self.x_ar + x * self.x_gap, self.y_ar + y * self.y_gap)
                    _draw_title(chart["title"], self.x_title + x * self.x_gap, self.y_title + y * self.y_gap)
                    _draw_achi(chart["achievements"], self.x_achi + x * self.x_gap, self.y_achi + y * self.y_gap)
                    _draw_inner_level(chart["inner_level"], self.x_level + x * self.x_gap,
                                      self.y_level + y * self.y_gap)
                    _draw_single_rating(chart["single_rating"], self.x_sin_rating + x * self.x_gap,
                                        self.y_sin_rating + y * self.y_gap)
                    i += 1
            queue.put(1)

        def _draw_new_list(queue: Queue):
            i = 0
            for y in range(3):
                if i >= len(self.best_list_response["records_new"]):
                    break
                for x in range(5):
                    if i >= len(self.best_list_response["records_new"]):
                        break
                    chart = self.best_list_response["records_new"][i]
                    _draw_difficulty_frame(chart["difficulty"], self.x_df + x * self.x_gap,
                                           self.y_df + y * self.y_gap + self.old_new_gap)
                    _draw_cover(chart["id"], self.x_cover + x * self.x_gap,
                                self.y_cover + y * self.y_gap + self.old_new_gap)
                    _draw_combo_sync_rank(chart["combo"], chart["sync"], self.x_csr + x * self.x_gap,
                                          self.y_csr + y * self.y_gap + self.old_new_gap)
                    _draw_chart_type(chart["chart_type"], self.x_ct + x * self.x_gap,
                                     self.y_ct + y * self.y_gap + self.old_new_gap)
                    _draw_achi_rank(chart["achi_rank"], self.x_ar + x * self.x_gap,
                                    self.y_ar + y * self.y_gap + self.old_new_gap)
                    _draw_title(chart["title"], self.x_title + x * self.x_gap,
                                self.y_title + y * self.y_gap + self.old_new_gap)
                    _draw_achi(chart["achievements"], self.x_achi + x * self.x_gap,
                               self.y_achi + y * self.y_gap + self.old_new_gap)
                    _draw_inner_level(chart["inner_level"], self.x_level + x * self.x_gap,
                                      self.y_level + y * self.y_gap + self.old_new_gap)
                    _draw_single_rating(chart["single_rating"], self.x_sin_rating + x * self.x_gap,
                                        self.y_sin_rating + y * self.y_gap + self.old_new_gap)
                    i += 1
            queue.put(1)

        def _draw_name_frame(queue: Queue):
            def _draw_dxrating():
                rank_img = Image.open(f"./material/rank_icon/UI_Rank_{self.best_list_response['rank_no']:02d}.png"). \
                    resize((100, 43))
                plate_img.paste(rank_img, (416, 9), mask=rank_img.split()[3])
                rating_frame_img = Image.open(f"./material/rating_box/"
                                              f"UI_CMN_DXRating_{self.frame_no}.png").resize((230, 45))
                plate_img.paste(rating_frame_img, (176, 9), mask=rating_frame_img.split()[3])
                dxrating_str = reversed(str(self.best_list_response['dx_rating']))
                for x, num in zip([355, 337, 319, 301, 283], dxrating_str):
                    num_img = Image.open(f"./material/numbers/{num}.png").resize((21, 25))
                    plate_img.paste(num_img, (x, 20), mask=num_img.split()[3])

                note_img = Image.open("./material/plates/UI_CMN_Shougou_Rainbow.png").resize((352, 46))
                plate_img.paste(note_img, (171, 116), mask=note_img.split()[3])
                font_note = ImageFont.truetype("./material/typeface/Dongqing.otf", 20, encoding="utf-8")
                if self.mode == "B40":
                    rating_note = f"Best 40: {self.best_list_response['rating']} + " \
                                  f"{self.best_list_response['rank_rating']}"
                else:
                    rating_note = f"Best 50 Simulation"
                len_x = font_note.getsize(rating_note)[0]
                plate_draw.text((171 + int((352 - len_x) / 2), 127), rating_note, "white", font=font_note,
                                stroke_width=2, stroke_fill="black")

            def _draw_name():
                white_frame_img = Image.open("./material/plates/UI_WhiteFrame.png").resize((345, 59))
                plate_img.paste(white_frame_img, (174, 59), mask=white_frame_img.split()[3])
                name_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 30, encoding="utf-8")
                nickname = ' '.join(self.best_list_response['nickname'])
                limit = lambda text: text if name_font.getsize(text)[0] <= 271 else limit(text[:-1])
                nickname = limit(nickname)
                plate_draw.text((193, 61), nickname, "black", name_font)
                if "qq" in self.payload:
                    try:
                        data = requests.get(f'http://q1.qlogo.cn/g?b=qq&nk={self.payload["qq"]}&s=640')
                        head_img = Image.open(BytesIO(data.content)).resize((143, 143))
                        head_img_mask = Image.open(f"./material/plates/UI_Icon_000001.png").resize((143, 143))
                        plate_img.paste(head_img, (12, 9), mask=head_img_mask)
                    finally:
                        pass

            # from server, version plate base
            if self.best_list_response['plate_id']:
                plate_file_name = self.best_list_response['plate_id']
            # customized plate base
            elif self.qq_id:
                user_plate = PlateSetting.get_or_none(PlateSetting.qq_id == self.qq_id)
                if user_plate:
                    plate_file_name = user_plate.plate_id
                else:
                    plate_file_name = "000001"
            else:
                plate_file_name = "000001"
            plate_img = Image.open(f"./material/plates/UI_Plate_{plate_file_name}.png")
            plate_img = plate_img.resize((1037, 167))
            plate_draw = ImageDraw.Draw(plate_img)
            _draw_name()
            _draw_dxrating()
            self.bg_img.paste(plate_img, (373, 18), mask=plate_img.split()[3])
            queue.put(1)

        q, i = Queue(), 0
        Process(target=_draw_old_list, args=(q,)).run()
        Process(target=_draw_new_list, args=(q,)).run()
        Process(target=_draw_name_frame, args=(q,)).run()
        while i != 3:
            if q.get():
                i += 1

    def get_pic(self):
        return self.bg_img


class Best40List(BestList):
    x_df, y_df = (25, 232)
    x_cover, y_cover = (41, 243)
    x_csr, y_csr = (314, 301)
    x_ct, y_ct = (40, 308)
    x_ar, y_ar = (306, 267)
    x_achi, y_achi = (140, 271)
    x_title, y_title = (141, 237)
    x_level, y_level = (245, 309)
    x_sin_rating, y_sin_rating = (253, 306)
    x_gap, y_gap = (375, 120)
    old_new_gap = 640
    mode = "B40"

    def __init__(self, username: str, qq_id: int):
        self.bg_img = Image.open("./material/background/B40-unip-lisa.png")
        super(Best40List, self).__init__(username, qq_id)

    def get_data_from_third(self):
        return super(Best40List, self).get_data_from_third()

    def translate_from_third(self):
        super(Best40List, self).translate_from_third()
        self.best_list_response["dx_rating"] = self.best_list_response["rating"] + \
                                               self.best_list_response["rank_rating"]

    def get_from_home(self, mode: str):
        if super(Best40List, self).get_from_home(mode):
            self.best_list_response["dx_rating"] = self.best_list_response["rating"]
            return True
        return False


class Best50List(BestList):
    x_df, y_df = (26, 213)
    x_cover, y_cover = (42, 224)
    x_csr, y_csr = (315, 281)
    x_ct, y_ct = (42, 289)
    x_ar, y_ar = (307, 248)
    x_achi, y_achi = (141, 252)
    x_title, y_title = (142, 219)
    x_level, y_level = (246, 289)
    x_sin_rating, y_sin_rating = (254, 286)
    x_gap, y_gap = (375, 110)
    old_new_gap = 810
    mode = "B50"

    def __init__(self, username: str, qq_id: int):
        self.bg_img = Image.open("./material/background/B50-unip-lisa.png")
        super(Best50List, self).__init__(username, qq_id)

    def get_data_from_third(self):
        self.payload["b50"] = True
        return super(Best50List, self).get_data_from_third()

    def translate_from_third(self):
        def _calculate_single_rating(achi_rank: str, achievements: float, inner_level: float):
            coef = {"SSSp": 22.4, "SSS": 21.6, "SSp": 21.1, "SS": 20.8, "Sp": 20.3, "S": 20,
                    "AAA": 16.8, "AA": 15.2, "A": 13.6, "BBB": 12.0, "BB": 11.2, "B": 9.6, "C": 8.0,
                    "D": (0, 1.6, 3.2, 4.8, 6.4)}
            sp_coef = {100.4999: 22.2, 99.9999: 21.4, 98.9999: 20.7, 96.9999: 19.8, 79.9999: 13.5}
            return int((100.5 if achievements > 100.5 else achievements) / 100 *
                       inner_level * (sp_coef[achievements] if achievements in sp_coef else coef[achi_rank]))

        super(Best50List, self).translate_from_third()
        for chart in self.best_list_response["records_old"]:
            chart["single_rating"] = _calculate_single_rating(chart["achi_rank"], chart["achievements"],
                                                              chart["inner_level"])
        self.best_list_response["records_old"].sort(key=lambda elem: elem["single_rating"], reverse=True)
        for chart in self.best_list_response["records_new"]:
            chart["single_rating"] = _calculate_single_rating(chart["achi_rank"], chart["achievements"],
                                                              chart["inner_level"])
        self.best_list_response["records_new"].sort(key=lambda elem: elem["single_rating"], reverse=True)
        self.best_list_response["rating"] = sum(chart["single_rating"]
                                                for chart in self.best_list_response["records_old"] +
                                                self.best_list_response["records_new"])
        self.best_list_response["dx_rating"] = self.best_list_response["rating"]

    def get_from_home(self, mode: str):
        if super(Best50List, self).get_from_home(mode):
            self.best_list_response["dx_rating"] = self.best_list_response["rating"]
            return True
        return False


def set_name_plate(user_in: str, user_id: int) -> str:
    regex = "设置姓名框 ([0-9]+)"
    [plate_id] = re.match(regex, user_in).groups()
    plate_id = plate_id.rjust(6, '0')
    plate = PlateInfo.select(PlateInfo.plate_name).where(PlateInfo.plate_id == plate_id).get()
    if user_id not in superuser and plate and plate.customizable and plate.enable:
        player = PlayerBasicInfo.get_or_none(PlayerBasicInfo.qq_id == user_id)
        if not player:
            user_plate = PlateSetting.get_or_create(qq_id=user_id)
            user_plate.plate_id = plate_id
            user_plate.save()
        else:
            player.plate_id = plate_id
            player.save()
        return "できました！"
    elif user_id in superuser and plate:
        player = PlayerBasicInfo.get_or_none(PlayerBasicInfo.qq_id == user_id)
        if not player:
            user_plate = PlateSetting.get_or_create(qq_id=user_id)
            user_plate.plate_id = plate_id
            user_plate.save()
        else:
            player.plate_id = plate_id
            player.save()
        return "できました！"
    else:
        return "好像没有这张姓名框？"


async def analyze_rating(user_in: str, user_id: int):
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

    # return [(achievement, inner_level), ]
    def _rating_to_inner_level(single_rating: int) -> list:
        ans = []
        achi_rank_coef = {"SSS+": 14.0, "SSS": 13.5, "SS+": 13.2, "SS": 13.0, "S+": 12.7, "S": 12.5, "AAA": 10.5,
                          "AA": 9.5, "A": 8.5, "BBB": 7.5, "BB": 7.0, "B": 6.0, "C": 5.0}
        inner_level_list = [1.0, 2.0, 3.0, 4.0, 5.0, 5.4, 5.6, 5.8]
        for achi_rank_trial in achi_rank_coef.keys():
            inner_level_trial = round(float(single_rating / achi_rank_coef[achi_rank_trial]
                                            / achie_ranks[achi_rank_trial] * 100), 1)
            single_rating_trial = int(inner_level_trial * achi_rank_coef[achi_rank_trial]
                                      * achie_ranks[achi_rank_trial] / 100)
            if single_rating_trial == single_rating and \
                    (6.0 <= inner_level_trial <= 15.0 or inner_level_trial in inner_level_list):
                ans.append((achie_ranks[achi_rank_trial], round(inner_level_trial, 1)))
            elif single_rating_trial > single_rating and \
                    (6.0 <= inner_level_trial - 0.1 <= 15.0 or inner_level_trial - 0.1 in inner_level_list) and \
                    int((inner_level_trial - 0.1) * achi_rank_coef[achi_rank_trial]
                        * achie_ranks[achi_rank_trial] / 100) == single_rating:
                ans.append((achie_ranks[achi_rank_trial], round(inner_level_trial - 0.1)))
            elif single_rating_trial < single_rating and \
                    (6.0 <= inner_level_trial + 0.1 <= 15.0 or inner_level_trial + 0.1 in inner_level_list) and \
                    int((inner_level_trial + 0.1) * achi_rank_coef[achi_rank_trial]
                        * achie_ranks[achi_rank_trial] / 100) == single_rating:
                ans.append((achie_ranks[achi_rank_trial], round(inner_level_trial + 0.1, 1)))
        return ans

    def _advice(charts: list, mode: str) -> str:
        if len(charts) not in [25, 15]:
            return "先打满谱面试试吧！\n"
        var_single_rating, var_achie, var_inner_level = np.var([chart['ra'] for chart in charts]), \
                                                        np.var([chart['achievements'] for chart in charts]), \
                                                        np.var([chart['ds'] for chart in charts])
        # 单曲 rating 方差
        if var_single_rating <= (10 if mode == "B25" else 13):
            # 定数方差
            if var_inner_level <= (0.9 if mode == "B25" else 1.2):
                # 达成率总体高低
                if all(chart['achievements'] < 100 for chart in charts):
                    return "好像都没有 SSS 加，先往上推推吧？\n"
                elif len([chart for chart in charts if chart['achievements'] < 100]) * 4 >= \
                        len([chart for chart in charts if chart['achievements'] >= 100]):
                    return "可以把没有 SSS 以上的推一推？\n"
                elif len([chart for chart in charts if chart['achievements'] < 100.5]) * 4 >= \
                        len([chart for chart in charts if chart['achievements'] >= 100.5]):
                    return "可以把没有 SSS+ 以上的推一推？\n"
                else:
                    return "可以越级试试高一点定数的谱面～\n"
            else:
                if all(chart['achievements'] < 100.5 for chart in charts):
                    return "把全部谱面达成率推一推？\n"
                else:
                    return "把没有 SSS+ 的谱面推一推？\n"
        else:
            if var_achie <= (1.4 if mode == "B25" else 1.9):
                if len([chart for chart in charts if chart['achievements'] < 100.5]) * 4 < \
                        len([chart for chart in charts if chart['achievements'] >= 100.5]):
                    return "试试打高一点定数的谱面提高下界？\n"
                elif len([chart for chart in charts if chart['achievements'] < 100.5]) * 4 >= \
                        len([chart for chart in charts if chart['achievements'] >= 100.5]):
                    return "试试把没有 SSS+ 的谱面都推一推？\n"
                else:
                    return "试试全部谱面达成率推一推？\n"
            else:
                if var_inner_level >= (1.2 if mode == "B25" else 1.5):
                    return "可以试试靠后的谱面提高达成率\n"
                else:
                    return "没有 SSS+ 的都可以试试推一推\n"

    def _recommand(charts: list, mode: str):
        ans, inlist_chart = [], set()
        for chart in charts:
            inlist_chart.add((chart["song_id"], chart["level_label"]))
        # 未到达 SSS+ 的推荐升1评级
        for chart in charts:
            if chart['achievements'] < 100.5:
                i = 1
                for i, aim_achi in enumerate(achie_ranks.values()):
                    if chart['achievements'] >= aim_achi:
                        break
                aim_achi = tuple(achie_ranks.values())[i - 1]
                ans.append(f"{difficulty_short[chart['level_index']]}{chart['ds']}  {chart['song_id']}  "
                           f"{chart['title']}  {aim_achi}%  "
                           f"Rating +{_cal_single_rating(aim_achi, chart['ds']) - chart['ra']}")
        # 获取最低单曲 rating，计算对应定数达成率
        level_achi_list = _rating_to_inner_level(charts[-1]['ra'])
        for achi, level in level_achi_list:
            # 固定达成率，提高定数
            if mode == "B25":
                recommend_charts = ChartDifficulty. \
                    select(ChartDifficulty.inner_level, ChartDifficulty.difficulty, SongInfo.id, SongInfo.title). \
                    join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                    where(ChartDifficulty.inner_level.between(level + 0.2, level + 0.4) &
                          (ChartDifficulty.version == "舞萌DX2022") & (SongInfo.china_version != '舞萌DX2022')).\
                    objects()
            else:
                recommend_charts = ChartDifficulty. \
                    select(ChartDifficulty.inner_level, ChartDifficulty.difficulty, SongInfo.id, SongInfo.title). \
                    join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                    where(ChartDifficulty.inner_level.between(level + 0.2, level + 0.4) &
                          (ChartDifficulty.version == "舞萌DX2022") & (SongInfo.china_version == '舞萌DX2022')).\
                    objects()
            ans += [f"{_get_difficulty_short(chart.difficulty)}{chart.inner_level}  {chart.id}  " \
                    f"{chart.title}  {achi}%  " \
                    f"Rating +{_cal_single_rating(achi, chart.inner_level) - charts[-1]['ra']}"
                    for chart in recommend_charts if (chart.id, chart.difficulty) not in inlist_chart if achi >= 97]
            # 固定或降低定数，提高一档达成率
            if mode == "B25":
                recommend_charts = ChartDifficulty. \
                    select(ChartDifficulty.inner_level, ChartDifficulty.difficulty, SongInfo.id, SongInfo.title). \
                    join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                    where(ChartDifficulty.inner_level.between(level - 0.1, level + 0.1) &
                          (ChartDifficulty.version == "舞萌DX2022") & (SongInfo.china_version != '舞萌DX2022'))
            else:
                recommend_charts = ChartDifficulty. \
                    select(ChartDifficulty.inner_level, ChartDifficulty.difficulty, SongInfo.id, SongInfo.title). \
                    join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                    where(ChartDifficulty.inner_level.between(level - 0.1, level + 0.1) &
                          (ChartDifficulty.version == "舞萌DX2022") & (SongInfo.china_version == '舞萌DX2022'))
            if achi < 100.5:
                for i, aim_achi in enumerate(achie_ranks.values()):
                    if achi >= aim_achi:
                        break
                aim_achi = tuple(achie_ranks.values())[i - 1]
                for chart in recommend_charts:
                    if (chart.songinfo.id, chart.difficulty) not in inlist_chart:
                        ans += [f"{_get_difficulty_short(chart.difficulty)}{chart.inner_level}  {chart.songinfo.id}  "
                                f"{chart.songinfo.title}  {aim_achi}%  "
                                f"Rating +{_cal_single_rating(aim_achi, chart.inner_level) - charts[-1]['ra']}"]
        return random.sample(ans, min(4, len(ans)))

    def _cal_single_rating(achi: float, inner_level: float) -> int:
        achi_rank_coef = {"SSS+": 14, "SSS": 13.5, "SS+": 13.2, "SS": 13.0, "S+": 12.7, "S": 12.5,
                          "AAA": 10.5, "AA": 9.5, "A": 8.5, "BBB": 7.5, "BB": 7.0, "B": 6.0,
                          "C": 5.0, "D": 0}
        achi_rank = None
        for achi_rank_trial in achie_ranks.keys():
            if achi >= achie_ranks[achi_rank_trial]:
                achi_rank = achi_rank_trial
                break
        achi = 100.5 if achi > 100.5 else achi
        return int(achi / 100 * achi_rank_coef[achi_rank] * float(inner_level))

    _, username = re.match("(底分|Ra|Rating)分析\s?(.+)?", user_in).groups()
    payload = {"username": username} if username else {"qq": str(user_id)}
    payload["version"] = all_versions
    data = await get_player_data(payload, "best")
    if isinstance(data, str):
        return data, None
    old_list, new_list = data["charts"]["sd"], data["charts"]["dx"]
    text = f"{data['nickname']} 的 Rating 组成如下：\n\n"
    if old_list:
        text += f"B25 Rating 总计为{sum([chart['ra'] for chart in old_list])}\n" \
                f"最高分{data['charts']['sd'][0]['ra']}，相当于 " \
                f"{' / '.join([f'{level} {achi}%' for achi, level in _rating_to_inner_level(old_list[0]['ra'])])}\n" \
                f"最低分{data['charts']['sd'][-1]['ra']}，相当于 " \
                f"{' / '.join([f'{level} {achi}%' for achi, level in _rating_to_inner_level(old_list[-1]['ra'])])}\n"
        text += _advice(old_list, "B25")
        text += f"随机推荐推分（仅供参考）：\n" + "\n".join(_recommand(old_list, "B25")) + "\n\n"
    if new_list:
        text += f"B15 Rating 总计为{sum([chart['ra'] for chart in new_list])}\n" \
                f"最高分{data['charts']['dx'][0]['ra']}，相当于 " \
                f"{' / '.join([f'{level} {achi}%' for achi, level in _rating_to_inner_level(new_list[0]['ra'])])}\n" \
                f"最低分{data['charts']['dx'][-1]['ra']}，相当于 " \
                f"{' / '.join([f'{level} {achi}%' for achi, level in _rating_to_inner_level(new_list[-1]['ra'])])}\n"
        text += _advice(new_list, "B15")
        text += f"随机推荐推分（仅供参考）：\n" + "\n".join(_recommand(new_list, "B15")) + "\n\n"
    text += "* 推荐结果为完全随机，LisaBot 不会对您的数据进行指向性推荐。\n" \
            "Analyzed by LisaBot, function developed by Koto(RINkoTO) & Ryan"
    return None, str(image_to_base64(text_to_image(text)), encoding="utf-8")
