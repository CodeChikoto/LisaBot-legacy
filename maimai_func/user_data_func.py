import json
import re
import random
from threading import Thread
from typing import Optional

import numpy as np
import requests
from models.player_models import *
from tools.image import *
from tools.shared_var import *
from math import ceil
from multiprocessing import Process

random.seed(2508)
translate_dict = {'fs': 'FS', 'fsp': 'FSp', 'fc': 'FC', 'fcp': 'FCp',
                  'fsd': 'FSD', 'fsdp': 'FSDp', 'ap': 'AP', 'app': 'APp', '': ''}
title_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 20, encoding="utf-8")
achi_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 24, encoding="utf-8")
level_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 14, encoding="utf-8")
sin_rating_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 18, encoding="utf-8")
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5OTM0MzM1NzcsInVzZXJfbmFtZSI6IlJJTmtvVE8iLCJleHAiOjE2ODg4OTE4ODEuMDcwOTIxLCJwZXJtaXNzaW9uIjoiYm90In0.tjjDFIdVYejgcTLsw8DEsPVozmwcPEP189xwXiH3jic"


def get_data_from_third(payload: dict, endpoint: str):
    try:
        with requests.post(url='https://www.diving-fish.com/api/maimaidxprober/query/' + endpoint,
                           proxies={'http': None, 'https': None},
                           json=payload) as resp:
            if resp.status_code == 400:
                data = "没有在第三方数据源找到玩家，也可能是没有绑定 QQ 号。"
            elif resp.status_code == 403:
                data = '这位好像不给获取信息捏。'
            elif resp.status_code == 200:
                data = resp.json()
            else:
                data = '发生了错误，找找机修看看吧？'
    except ConnectionError:
        data = '连接失败，重试一下或者找找机修吧？'
    return data


def get_data_from_home(payload: dict, endpoint: str):
    try:
        resp = requests.get(url="http://154.86.19.207:8000/player_query/" + endpoint,
                            headers={"token": token},
                            proxies={'http': None, 'https': None},
                            data=json.dumps(payload))
        if resp.status_code != 200:
            return False, resp.text
        else:
            return True, resp.json()
    except ConnectionError:
        return False, None


class LevelList(Thread):
    def __init__(self, username: str, qq_id: int, level: str, page: int):
        super(LevelList, self).__init__()
        self.level_list_response = {"records": [], "nickname": None}
        self.error = None
        self.username = username
        self.qq_id = qq_id
        self.level = level
        self.page = page
        self.image = None

    def get_from_home(self):
        request_data = {"username": self.username, "qq_id": None} if self.username \
            else {'qq_id': self.qq_id, "username": None}
        request_data["level"] = self.level
        success, data = get_data_from_home(request_data, "level_achievements")
        if success:
            self.level_list_response = data
            return True
        else:
            self.error = data
            return False

    def get_from_third(self):
        def _find_aim_level():
            for chart in data["verlist"]:
                if chart["level"] == self.level:
                    ans = {
                        "title": chart["title"],
                        "chart_type": chart["type"],
                        "achievements": chart['achievements'],
                        "combo": combo_upper[chart['fc']],
                        "difficulty": difficulty_alias[difficulty_short[chart["level_index"]].lower()],
                        "id": chart["id"]
                    }
                    inner_level = ChartDifficulty. \
                        select(ChartDifficulty.inner_level). \
                        join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                        where((SongInfo.id == ans["id"]) &
                              (SongInfo.chart_type == ans["chart_type"]) &
                              (ChartDifficulty.difficulty == ans["difficulty"]) &
                              (ChartDifficulty.version == "舞萌DX2022")). \
                        get(). \
                        inner_level
                    ans["inner_level"] = inner_level
                    self.level_list_response["records"].append(ans)

        payload = {"username": self.username} if self.username else {'qq': str(self.qq_id)}
        payload["version"] = all_versions
        data = get_data_from_third(payload, "plate")
        if isinstance(data, str):
            self.error += "\n" + data
            return False
        _find_aim_level()
        self.level_list_response["records"].sort(key=lambda item: item["achievements"], reverse=True)
        return True

    def generate_pic(self):
        if not self.level_list_response["records"]:
            self.error = "真的打过这个等级么？"
        total_pages = ceil(len(self.level_list_response["records"]) / 25)
        records = self.level_list_response["records"][25 * (self.page - 1):
                                                      min(25 * self.page, len(self.level_list_response["records"]))]
        msg = f"你的等级{self.level}达成率列表第{self.page}/{total_pages}页如下："
        for record in records:
            if not record['combo']:
                record['combo'] = ''
            else:
                record['combo'] = record['combo'].replace('p', '+')
            msg += f"\n{record['achievements']:8.4f}  {record['combo']:3}  {record['chart_type']}  " \
                   f"{difficulty_short[record['difficulty']]}{record['inner_level']}  {record['title']}"
        msg += f"\nCreated by LisaBot, maintained by RINkoTO"
        self.image = str(image_to_base64(text_to_image(msg)), encoding="utf-8")

    def run(self):
        if self.get_from_home() or self.get_from_third():
            self.generate_pic()

    def get_result(self):
        return self.error, self.image


async def get_level_achievements_list(user_in: str, user_id: int):
    regex = "^(分数|达成率)列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?"
    _, level, page, username = re.match(regex, user_in).groups()
    page = 1 if not page else int(page)
    level_list = LevelList(username, user_id, level, page)
    level_list.start()
    level_list.join()
    return level_list.get_result()


class LevelProcess(Thread):
    def __init__(self, username: str, qq_id: int, level: str, achievements_rank: str, combo_rank: str, sync_rank: str):
        super(LevelProcess, self).__init__()
        self.total_amount = 0
        self.finished_amount = 0
        self.level_list_response = {"records": [], "nickname": None}
        self.unfinished_charts = []
        self.error = None
        self.username = username
        self.qq_id = qq_id
        self.level = level
        self.achievements_rank = achievements_rank
        self.combo_rank = combo_rank
        self.sync_rank = sync_rank
        self.message = None

    def get_from_home(self):
        request_data = {"username": self.username, "qq_id": None} if self.username \
            else {'qq_id': self.qq_id, "username": None}
        request_data["level"] = self.level
        success, data = get_data_from_home(request_data, "level_achievements")
        if success:
            self.level_list_response = data
            return True
        else:
            self.error = data
            return False

    def get_from_third(self):
        def _find_aim_level():
            for chart in data["verlist"]:
                if chart["level"] == self.level:
                    self.level_list_response["records"].append({
                        "id": chart["id"],
                        "title": chart["title"],
                        "achievements": chart['achievements'],
                        "combo": combo_upper[chart['fc']],
                        "sync": sync_upper[chart['fs']],
                        "difficulty": difficulty_alias[difficulty_short[chart["level_index"]].lower()],
                    })

        payload = {"username": self.username} if self.username else {'qq': str(self.qq_id)}
        payload["version"] = all_versions
        data = get_data_from_third(payload, "plate")
        if isinstance(data, str):
            self.error += "\n" + data
            return False
        self.error = ""
        _find_aim_level()
        self.level_list_response["records"].sort(key=lambda x: x["achievements"], reverse=True)
        return True

    def get_level_amount(self) -> bool:
        row = ChartDifficulty. \
            select(fn.COUNT(ChartDifficulty.id).alias('count')). \
            where((ChartDifficulty.level == self.level) & (ChartDifficulty.version == '舞萌DX2022')). \
            get()
        if not row:
            self.error = "本当にこのレベルが有りますか？"
            return False
        else:
            self.total_amount = row.count
            return True

    def find_finished(self):
        if self.achievements_rank:
            aim_achievements = achievements_ranks[self.achievements_rank]
        if self.combo_rank:
            aim_combo = combo_ranks[self.combo_rank]
        if self.sync_rank:
            aim_sync = sync_ranks[self.sync_rank]
        finished_charts = self.level_list_response["records"]
        if self.achievements_rank:
            finished_charts = list(filter(lambda chart: chart["achievements"] >= aim_achievements, finished_charts))
        if self.combo_rank:
            finished_charts = list(filter(lambda chart: chart["combo"] and combo_ranks[chart["combo"]] <= aim_combo,
                                          finished_charts))
        if self.sync_rank:
            finished_charts = list(filter(lambda chart: chart["sync"] and sync_ranks[chart["sync"]] <= aim_sync,
                                          finished_charts))
        self.unfinished_charts = list(filter(lambda chart: chart not in finished_charts,
                                             self.level_list_response["records"]))
        self.finished_amount = len(finished_charts)

    def generate_message(self):
        if self.finished_amount == self.total_amount:
            self.message = f"{self.total_amount}张谱全部完成！おめでとう～"
        else:
            message = f"你的 {self.level} {self.achievements_rank if self.achievements_rank else ''} " \
                      f"{self.combo_rank if self.combo_rank else ''} {self.sync_rank if self.sync_rank else ''} 完成进度" \
                      f"{self.finished_amount}/{self.total_amount}\n" \
                      f"まだ{self.total_amount - self.finished_amount}残ります〜\n"
            if len(self.unfinished_charts) < 5:
                message += f"已游玩但为达成目标谱面包括："
                for record in self.unfinished_charts:
                    message += f"\n{difficulty_short[record['difficulty']]}  {record['id']}  {record['title']}"
            self.message = message

    def run(self) -> None:
        if self.get_level_amount() and (self.get_from_home() or self.get_from_third()):
            self.find_finished()
            self.generate_message()

    def get_message(self):
        return self.message if self.message else self.error


async def get_level_process(user_in: str, user_id: int):
    regex = "^进度 ([0-9]+\+?) " + combo_ranks_regex + "?\s?" \
            + sync_ranks_regex + "?\s?" + achievements_ranks_regex + "?\s?(.+)?"
    [level, combo, sync, achievements_rank, username] = re.match(regex, user_in.upper()).groups()
    if not achievements_rank and not combo and not sync:
        return "何が知りたい？"
    level_process = LevelProcess(username, user_id, level, achievements_rank, combo, sync)
    level_process.start()
    level_process.join()
    return level_process.get_message()


class PlateProcess(Thread):
    def __init__(self, plate_name: str, username: str, qq_id: int):
        super(PlateProcess, self).__init__()
        self.message = None
        self.plate_process_response = {"unfinished_charts": [],
                                       "requirement": "",
                                       "total_amount": {},
                                       "finished_amount": {}}
        self.error = None
        self.required_charts = set()
        self.plate = None
        self.version_short = None
        self.plate_name = plate_name
        self.username = username
        self.qq_id = qq_id

    def verify_plate_available(self) -> bool:
        def _translate_to_ja(source: str):
            ja = {"晓": "暁", "樱": "櫻", "堇": "菫", "辉": "輝", "霸": "覇", "华": "華", "极": "極", "酱": "将"}
            for char in source:
                if char in ja:
                    source = source.replace(char, ja[char])
            return source

        self.plate_name = _translate_to_ja(self.plate_name)
        self.plate = PlateInfo.get_or_none(PlateInfo.plate_name == self.plate_name)
        if not self.plate:
            return False
        self.version_short = self.plate_name[0] if self.plate_name != "覇者" else "舞"
        return True

    def get_from_third(self) -> bool:
        def _finished(chart: dict):
            if self.plate.requirement in achievements_ranks.keys():
                return chart["achievements"] >= achievements_ranks[self.plate.requirement]
            elif self.plate.requirement in combo_ranks.keys():
                return combo_ranks[combo_upper[chart["fc"]]] <= combo_ranks[self.plate.requirement]
            elif self.plate.requirement in sync_ranks.keys():
                return sync_ranks[sync_upper[chart["fs"]]] <= sync_ranks[self.plate.requirement]

        self.get_plate_charts_amount()
        payload = {"version": version_alias[self.version_short][2]}
        if self.username:
            payload["username"] = self.username
        else:
            payload["qq"] = self.qq_id
        data = get_data_from_third(payload, "plate")
        if isinstance(data, str):
            self.error += "\n" + data
            return False
        data["verlist"] = \
            list(
                filter(lambda chart: (chart["id"], difficulty_alias[difficulty_short[chart["level_index"]].lower()]) in self.required_charts,
                       (data["verlist"])))
        finished_charts = list(filter(_finished, data["verlist"]))
        for chart in list(filter(lambda c: c not in finished_charts, data["verlist"])):
            self.plate_process_response["unfinished_charts"]. \
                append({"id": chart["id"],
                        "difficulty": difficulty_alias[difficulty_short[chart["level_index"]].lower()],
                        "title": chart["title"]})
        for difficulty in ("Basic", "Advanced", "Expert", "Master", "Re:MASTER"):
            self.plate_process_response["finished_amount"][difficulty] = \
                sum(1 for _ in filter(lambda chart: difficulty_alias[difficulty_short[chart["level_index"]].lower()] == difficulty,
                                      finished_charts))
        return True

    def get_from_home(self):
        request_data = {"username": self.username, "qq_id": None} if self.username \
            else {'qq_id': self.qq_id, "username": None}
        request_data['plate_name'] = self.plate_name
        success, data = get_data_from_home(request_data, "check_plate_process")
        if success:
            self.plate_process_response = data
            return True
        else:
            self.error = data
            return False

    def get_plate_charts_amount(self):
        rows = ChartInfo. \
            select(ChartInfo.difficulty, fn.COUNT(ChartInfo.id).alias('chart_amount')). \
            join(ChartDifficulty, on=(ChartInfo.id == ChartDifficulty.id) &
                                     (ChartInfo.difficulty == ChartDifficulty.difficulty)). \
            switch(ChartInfo). \
            join(PlateInfo, on=(ChartInfo.plate_mask.bin_and(PlateInfo.version_mask))). \
            where((ChartDifficulty.version == '舞萌DX2022') &
                  (PlateInfo.plate_name == self.plate_name)). \
            group_by(ChartDifficulty.difficulty). \
            objects()
        self.plate_process_response["total_amount"] = {row.difficulty: row.chart_amount for row in rows}
        required_charts = ChartInfo. \
            select(ChartInfo.id, ChartInfo.difficulty). \
            join(ChartDifficulty, on=(ChartInfo.id == ChartDifficulty.id) &
                                     (ChartInfo.difficulty == ChartDifficulty.difficulty)). \
            switch(ChartInfo). \
            join(PlateInfo, on=(ChartInfo.plate_mask.bin_and(PlateInfo.version_mask))). \
            where((ChartDifficulty.version == '舞萌DX2022') &
                  (PlateInfo.plate_name == self.plate_name)). \
            objects()
        self.required_charts = set((chart.id, chart.difficulty) for chart in required_charts)

    def generate_message(self):
        message = f"{self.plate_name}的要求是 {self.plate.requirement}\n" \
                  f"你的{self.plate_name}完成情况如下：\n"
        if sum(self.plate_process_response["finished_amount"].values()) == \
                sum(self.plate_process_response["total_amount"].values()):
            message += f"不剩！できました、おめでとう！"
        else:
            message += f"已完成{sum(self.plate_process_response['finished_amount'].values())}" \
                       f"/{sum(self.plate_process_response['total_amount'].values())}，" \
                       f"剩余{sum(self.plate_process_response['total_amount'].values()) - sum(self.plate_process_response['finished_amount'].values())}\n" \
                       f"各难度剩余情况如下：\n"
            for diff in ("Basic", "Advanced", "Expert", "Master", "Re:MASTER"):
                if diff not in self.plate_process_response["total_amount"]:
                    break
                message += f"{diff} {self.plate_process_response['total_amount'][diff] - self.plate_process_response['finished_amount'][diff]}\n"
            if 0 < len(self.plate_process_response['unfinished_charts']) < 5:
                message += f"已游玩但未达成谱面如下：\n"
                for chart in self.plate_process_response['unfinished_charts']:
                    message += f"{chart['difficulty']}  {chart['id']}  {chart['title']}\n"
            message += f"拼机最快需要{ceil((sum(self.plate_process_response['total_amount'].values()) - sum(self.plate_process_response['finished_amount'].values())) / 4)}局"
            if self.plate.requirement != "FSD":
                message += f"，单刷最快需要{ceil((sum(self.plate_process_response['total_amount'].values()) - sum(self.plate_process_response['finished_amount'].values())) / 3)}局\n"
            message += "\n頑張ってね！"
        self.message = message

    def run(self) -> None:
        if self.verify_plate_available() and (self.get_from_home() or self.get_from_third()):
            self.generate_message()

    def get_message(self):
        return self.message if self.message else self.error


async def get_plate_process(user_in: str, qq_id: int) -> Optional[str]:
    regex = "^(.+)进度\s?(.+)?"
    plate_name, username = re.match(regex, user_in).groups()
    plate_process = PlateProcess(plate_name, username, qq_id)
    plate_process.start()
    plate_process.join()
    return plate_process.get_message()


def get_song_best():
    pass


class BestList(Thread):
    text_message: str
    error: Optional[str]
    payload: dict
    best_list_response: dict
    username: str
    qq_id: int
    frame_no: str
    bg_img: Optional[Image.Image]
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
        super(BestList, self).__init__()
        self.payload = {"version": all_versions}
        self.username, self.qq_id = username, qq_id
        self.error = None

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

    def get_from_third(self) -> bool:
        if self.username:
            self.payload["username"] = self.username
        elif self.qq_id:
            self.payload["qq"] = str(self.qq_id)
        else:
            self.error = "QQ 号和用户名都获取不到，怎么回事呢？"
        resp = get_data_from_third(self.payload, "player")
        if isinstance(resp, str):
            self.error += "\n" + resp
            return False
        else:
            self.best_list_response = resp
            self.translate_from_third()
            return True

    def get_from_home(self) -> bool:
        request_data = {"username": self.username, "qq_id": None} if self.username \
            else {'qq_id': self.qq_id, "username": None}
        request_data['mode'] = self.mode
        success, data = get_data_from_home(request_data, "best_records")
        if success:
            self.best_list_response = data
            return True
        else:
            self.error = data
            return False

    def specific_frame(self):
        mode = self.mode
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
            bg_drawer.text((x - level_font.getsize(f"{inner_level} ▶")[0], y), f"{inner_level} ▶", "black",
                           level_font)

        # 单曲 rating
        def _draw_single_rating(single_rating: int, x: int, y: int):
            bg_drawer.text((x, y), f"{single_rating}", "black", sin_rating_font)

        def _draw_old_list():
            i = 0
            for y in range(7):
                if i >= len(self.best_list_response["records_old"]):
                    break
                for x in range(5):
                    if i >= len(self.best_list_response["records_old"]):
                        break
                    chart = self.best_list_response["records_old"][i]
                    _draw_difficulty_frame(chart["difficulty"], self.x_df + x * self.x_gap,
                                           self.y_df + y * self.y_gap)
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

        def _draw_new_list():
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

        def _draw_name_frame():
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
                if not self.username:
                    try:
                        data = requests.get(f'http://q1.qlogo.cn/g?b=qq&nk={self.qq_id}&s=640')
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

        threads = [Thread(target=_draw_old_list, args=()),
                   Thread(target=_draw_new_list, args=()),
                   Thread(target=_draw_name_frame, args=())]
        for thread in threads:
            thread.start()
            thread.join()

    def run(self) -> None:
        if self.get_from_home() or self.get_from_third():
            self.specific_frame()
            self.draw_pic()
        else:
            self.bg_img = None

    def get_message(self):
        if self.bg_img:
            return str(image_to_base64(self.bg_img), encoding="utf-8"), None
        else:
            return None, self.error


async def get_best_list(user_in: str, qq_id: int):
    _, mode, username = re.match("^(b|B)(4|5)0\s?(.+)?", user_in).groups()
    mode = "B40" if mode == "4" else "B50"
    best_list = Best40List(username, qq_id) if mode == "B40" else Best50List(username, qq_id)
    best_list.start()
    best_list.join()
    return best_list.get_message()


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

    def get_from_third(self):
        return super(Best40List, self).get_from_third()

    def translate_from_third(self):
        super(Best40List, self).translate_from_third()
        self.best_list_response["dx_rating"] = self.best_list_response["rating"] + \
                                               self.best_list_response["rank_rating"]

    def get_from_home(self):
        if super(Best40List, self).get_from_home():
            self.best_list_response["dx_rating"] = self.best_list_response["rating"] + \
                                                   self.best_list_response["rank_rating"]
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

    def get_from_third(self):
        self.payload["b50"] = True
        return super(Best50List, self).get_from_third()

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

    def get_from_home(self):
        if super(Best50List, self).get_from_home():
            self.best_list_response["dx_rating"] = self.best_list_response["rating"]
            return True
        return False


async def set_name_plate(user_in: str, user_id: int) -> str:
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


class RatingAnalysis(Thread):
    def __init__(self, username: str, qq_id: int):
        super(RatingAnalysis, self).__init__()
        self.image = None
        self.error = None
        self.payload = {"version": all_versions}
        self.username, self.qq_id = username, qq_id
        self.best_list_response = {}

    def translate_from_third(self):
        self.best_list_response["rank_rating"] = self.best_list_response["additional_rating"]
        self.best_list_response["records_old"] = self.best_list_response["charts"]["sd"]
        self.best_list_response["records_new"] = self.best_list_response["charts"]["dx"]
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
        self.best_list_response["rating_old"] = \
            sum([chart["single_rating"] for chart in self.best_list_response["records_old"]])
        self.best_list_response["rating_new"] = \
            sum([chart["single_rating"] for chart in self.best_list_response["records_new"]])

    def get_from_third(self) -> bool:
        if self.username:
            self.payload["username"] = self.username
        elif self.qq_id:
            self.payload["qq"] = str(self.qq_id)
        else:
            self.error = "QQ 号和用户名都获取不到，怎么回事呢？"
        resp = get_data_from_third(self.payload, "player")
        if isinstance(resp, str):
            self.error += "\n" + resp
            return False
        else:
            self.best_list_response = resp
            self.translate_from_third()
            return True

    def get_from_home(self) -> bool:
        return False
        request_data = {"username": self.username, "qq_id": None} if self.username \
            else {'qq_id': self.qq_id, "username": None}
        request_data['mode'] = "B40"
        try:
            resp = requests.get("http://154.86.19.207:8000/player_query/best_records", headers={"token": token},
                                proxies={'http': None, 'https': None}, data=json.dumps(request_data))
            if resp.status_code != 200:
                self.error = resp.text
                return False
            else:
                self.best_list_response = resp.json()
            return True
        except ConnectionError:
            return False

    @staticmethod
    def _rating_to_inner_level(single_rating: int) -> list:
        ans = []
        achi_rank_coef = {"SSS+": 14.0, "SSS": 13.5, "SS+": 13.2, "SS": 13.0, "S+": 12.7, "S": 12.5, "AAA": 10.5,
                          "AA": 9.5, "A": 8.5, "BBB": 7.5, "BB": 7.0, "B": 6.0, "C": 5.0}
        inner_level_list = [1.0, 2.0, 3.0, 4.0, 5.0, 5.4, 5.6, 5.8]
        for achi_rank_trial in achi_rank_coef.keys():
            inner_level_trial = round(float(single_rating / achi_rank_coef[achi_rank_trial]
                                            / achievements_ranks[achi_rank_trial] * 100), 1)
            single_rating_trial = int(inner_level_trial * achi_rank_coef[achi_rank_trial]
                                      * achievements_ranks[achi_rank_trial] / 100)
            if single_rating_trial == single_rating and \
                    (6.0 <= inner_level_trial <= 15.0 or inner_level_trial in inner_level_list):
                ans.append((achievements_ranks[achi_rank_trial], round(inner_level_trial, 1)))
            elif single_rating_trial > single_rating and \
                    (6.0 <= inner_level_trial - 0.1 <= 15.0 or inner_level_trial - 0.1 in inner_level_list) and \
                    int((inner_level_trial - 0.1) * achi_rank_coef[achi_rank_trial]
                        * achievements_ranks[achi_rank_trial] / 100) == single_rating:
                ans.append((achievements_ranks[achi_rank_trial], round(inner_level_trial - 0.1)))
            elif single_rating_trial < single_rating and \
                    (6.0 <= inner_level_trial + 0.1 <= 15.0 or inner_level_trial + 0.1 in inner_level_list) and \
                    int((inner_level_trial + 0.1) * achi_rank_coef[achi_rank_trial]
                        * achievements_ranks[achi_rank_trial] / 100) == single_rating:
                ans.append((achievements_ranks[achi_rank_trial], round(inner_level_trial + 0.1, 1)))
        return ans

    @staticmethod
    def _advice(charts: list, mode: str) -> str:
        if len(charts) not in [25, 15]:
            return "先打满谱面试试吧！\n"
        var_single_rating = np.var([chart['single_rating'] for chart in charts])
        var_achie = np.var([chart['achievements'] for chart in charts])
        var_inner_level = np.var([chart['inner_level'] for chart in charts])
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
                if var_inner_level >= (1.2 if mode == "B25" else 1.6):
                    return "可以试试靠后的谱面提高达成率\n"
                else:
                    return "没有 SSS+ 的都可以试试推一推\n"

    def _recommand(self, charts: list, mode: str):
        def _cal_single_rating(achi: float, inner_level: float) -> int:
            achi_rank_coef = {"SSS+": 14, "SSS": 13.5, "SS+": 13.2, "SS": 13.0, "S+": 12.7, "S": 12.5,
                              "AAA": 10.5, "AA": 9.5, "A": 8.5, "BBB": 7.5, "BB": 7.0, "B": 6.0,
                              "C": 5.0, "D": 0}
            achi_rank = None
            for achi_rank_trial in achievements_ranks.keys():
                if achi >= achievements_ranks[achi_rank_trial]:
                    achi_rank = achi_rank_trial
                    break
            achi = 100.5 if achi > 100.5 else achi
            return int(achi / 100 * achi_rank_coef[achi_rank] * float(inner_level))

        ans, inlist_chart = [], set()
        for chart in charts:
            inlist_chart.add((chart["id"], chart["difficulty"]))
        # 未到达 SSS+ 的推荐升1评级
        for chart in charts:
            if chart['achievements'] < 100.5:
                i = 1
                for i, aim_achi in enumerate(achievements_ranks.values()):
                    if chart['achievements'] >= aim_achi:
                        break
                aim_achi = tuple(achievements_ranks.values())[i - 1]
                ans.append(f"{difficulty_short[chart['difficulty']]}{chart['inner_level']}  {chart['id']}  "
                           f"{chart['title']}  {aim_achi}%  "
                           f"Rating +{_cal_single_rating(aim_achi, chart['inner_level']) - chart['single_rating']}")
        # 获取最低单曲 rating，计算对应定数达成率
        level_achi_list = self._rating_to_inner_level(charts[-1]['single_rating'])
        for achi, level in level_achi_list:
            # 固定达成率，提高定数
            if mode == "B25":
                recommend_charts = ChartDifficulty. \
                    select(ChartDifficulty.inner_level, ChartDifficulty.difficulty, SongInfo.id, SongInfo.title). \
                    join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                    where(ChartDifficulty.inner_level.between(level + 0.2, level + 0.4) &
                          (ChartDifficulty.version == "舞萌DX2022") & (SongInfo.china_version != '舞萌DX2022')). \
                    objects()
            else:
                recommend_charts = ChartDifficulty. \
                    select(ChartDifficulty.inner_level, ChartDifficulty.difficulty, SongInfo.id, SongInfo.title). \
                    join(SongInfo, on=(ChartDifficulty.id == SongInfo.id)). \
                    where(ChartDifficulty.inner_level.between(level + 0.2, level + 0.4) &
                          (ChartDifficulty.version == "舞萌DX2022") & (SongInfo.china_version == '舞萌DX2022')). \
                    objects()
            ans += [f"{difficulty_short[chart.difficulty]}{chart.inner_level}  {chart.id}  " \
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
                for i, aim_achi in enumerate(achievements_ranks.values()):
                    if achi >= aim_achi:
                        break
                aim_achi = tuple(achievements_ranks.values())[i - 1]
                for chart in recommend_charts:
                    if (chart.songinfo.id, chart.difficulty) not in inlist_chart:
                        ans += [
                            f"{difficulty_short[chart.difficulty]}{chart.inner_level}  {chart.songinfo.id}  "
                            f"{chart.songinfo.title}  {aim_achi}%  "
                            f"Rating +{_cal_single_rating(aim_achi, chart.inner_level) - charts[-1]['ra']}"]
        return random.sample(ans, min(4, len(ans)))

    def generate_message(self):
        message = f"{self.best_list_response['nickname']} 的 Rating 组成如下：\n\n"
        if self.best_list_response["records_old"]:
            message += f"B25 Rating 总计为{self.best_list_response['rating_old']}\n" \
                       f"最高分{self.best_list_response['records_old'][0]['single_rating']}，相当于 " \
                       f"{' / '.join([f'{level} {achi}%' for achi, level in self._rating_to_inner_level(self.best_list_response['records_old'][0]['single_rating'])])}\n" \
                       f"最低分{self.best_list_response['records_old'][-1]['single_rating']}，相当于 " \
                       f"{' / '.join([f'{level} {achi}%' for achi, level in self._rating_to_inner_level(self.best_list_response['records_old'][-1]['single_rating'])])}\n"
            message += self._advice(self.best_list_response["records_old"], "B25")
            message += f"随机推荐推分（仅供参考）：\n" + "\n".join(
                self._recommand(self.best_list_response["records_old"], "B25")) + "\n\n"
        if self.best_list_response["records_new"]:
            message += f"B15 Rating 总计为{self.best_list_response['rating_new']}\n" \
                       f"最高分{self.best_list_response['records_new'][0]['single_rating']}，相当于 " \
                       f"{' / '.join([f'{level} {achi}%' for achi, level in self._rating_to_inner_level(self.best_list_response['records_new'][0]['single_rating'])])}\n" \
                       f"最低分{self.best_list_response['records_new'][-1]['single_rating']}，相当于 " \
                       f"{' / '.join([f'{level} {achi}%' for achi, level in self._rating_to_inner_level(self.best_list_response['records_new'][-1]['single_rating'])])}\n"
            message += self._advice(self.best_list_response['records_new'], "B15")
            message += f"随机推荐推分（仅供参考）：\n" + "\n".join(
                self._recommand(self.best_list_response['records_new'], "B15")) + "\n\n"
        message += "* 推荐结果为完全随机，LisaBot 不会对您的数据进行指向性推荐。\n" \
                   "Analyzed by LisaBot, function developed by Koto(RINkoTO) & Ryan"
        self.image = str(image_to_base64(text_to_image(message)), encoding="utf-8")

    def run(self) -> None:
        if self.get_from_home() or self.get_from_third():
            self.generate_message()

    def get_message(self):
        if self.image:
            return None, self.image
        else:
            return self.error, None


async def get_rating_analysis(user_in: str, user_id: int):
    regex = "^(底分|Ra|Rating|ra|rating)分析\s?(.+)?"
    _, username = re.match(regex, user_in).groups()
    rating_analysis = RatingAnalysis(username, user_id)
    rating_analysis.start()
    rating_analysis.join()
    return rating_analysis.get_message()


async def answer_analysis_request_from_others(items, request_user_id: int):
    if request_user_id in allowed_users:
        for item in items:
            if item.type == "at":
                return await get_rating_analysis("Ra分析", int(item.data["qq"]))
