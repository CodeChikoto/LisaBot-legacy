import random
import re
from decimal import Decimal
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from tools.get_player_data import *
from re import match
from tools.image import *
from tools.shared_var import *
import os
from functools import lru_cache
from multiprocessing import Process, Queue
from _thread import allocate_lock, start_new_thread


class BestList:
    def __init__(self, payload: dict, mode: str):
        self.rank_rating, self.rating, self.dx_rating = 0, 0, 0
        self.nickname, self.plate = "", None
        self.payload = payload
        self.mode = mode
        self.bg_path = "./material/background/B40-unip-lisa.png" if self.mode == "B40" \
            else "./material/background/B50-unip-lisa.png"
        self.bg_img = Image.open(self.bg_path)
        self.bg_draw = ImageDraw.Draw(self.bg_img)
        self.old_list, self.new_list = [], []
        self.error = ""

    # Nickname, B40 Rating, Rank
    async def get_basic_info(self) -> bool:
        data = await get_player_data(self.payload, "best")
        if isinstance(data, dict):
            self.rank_rating = data["additional_rating"]
            self.nickname = data["nickname"]
            self.rating = data["rating"]
            self.dx_rating = self.rank_rating + self.rating
            self.old_list, self.new_list = data["charts"]["sd"], data["charts"]["dx"]
            self.plate = data["plate"]
            return True
        else:
            self.error = data
            return False

    async def get_best_50(self) -> bool:
        def _fill_info(start: int, end: int, lock):
            nonlocal charts
            index_to_str = {0: "Basic", 1: "Advanced", 2: "Expert", 3: "Master", 4: "Re:MASTER"}
            conn = mai_dbpool.connection()
            cursor = conn.cursor()
            for chart in charts[start:end]:
                difficulty = index_to_str[chart["level_index"]]
                title_rep = chart["title"].replace("'", "\\'")
                cursor.execute(f"SELECT CD.Id,CD.InnerLevel,SI.ChinaVersion FROM ChartDifficulty CD JOIN SongInfo SI "
                               f"ON CD.Id=SI.Id WHERE SI.Title='{title_rep}' AND SI.ChartType='{chart['type']}' "
                               f"AND CD.Difficulty='{difficulty}' AND CD.Version='舞萌DX 2021'")
                [id, inner_level, china_version] = cursor.fetchone()
                chart["ds"] = float(inner_level)
                chart["ra"], chart["rate"] = _cal_single_rating(chart["achievements"], inner_level)
                chart["level_label"], chart["song_id"] = difficulty, id
                if china_version == "舞萌DX 2021":
                    self.new_list.append(chart)
                else:
                    self.old_list.append(chart)
            conn.close()
            lock.release()

        def _cal_single_rating(achi: float, inner_level: float) -> (int, str):
            achi_rank_coef = {"SSS+": 22.4, "SSS": 21.6, "SS+": 21.1, "SS": 20.8, "S+": 20.3, "S": 20.0,
                              "AAA": 16.8, "AA": 15.2, "A": 13.6, "BBB": 12.0, "BB": 11.2, "B": 9.6,
                              "C": 8.0, "D": 0}
            achi_rank = None
            for achi_rank_trial in achie_ranks.keys():
                if achi >= achie_ranks[achi_rank_trial]:
                    achi_rank = achi_rank_trial
                    break
            achi = 100.5 if achi > 100.5 else achi
            single_rating = int(achi / 100 * achi_rank_coef[achi_rank] * float(inner_level))
            return single_rating, achi_rank.lower().replace('+', 'p')

        self.old_list, self.new_list = [], []
        data = await get_player_data(self.payload, "plate")
        if isinstance(data, dict):
            charts, clear = data["verlist"], len(data["verlist"])
            locks_list = []
            for i in range(cpu_thread_amount):
                lock = allocate_lock()
                lock.acquire()
                locks_list.append(lock)
                Process(target=_fill_info, args=(int(clear / cpu_thread_amount * i),
                                                 int(clear / cpu_thread_amount * (i + 1)),
                                                 locks_list[i])).run()
            while any(lock.locked() for lock in locks_list):
                pass
            self.old_list.sort(key=lambda x: x["ra"], reverse=True)
            self.new_list.sort(key=lambda x: x["ra"], reverse=True)
            self.old_list, self.new_list = self.old_list[0:35], self.new_list[0:15]
            self.dx_rating = self.rating = sum(chart["ra"] for chart in self.old_list + self.new_list)
            return True
        else:
            self.error = data
            return False

    def draw_list(self, queue: Queue):
        combo_sync_file = {"fcp": "FCp", "fc": "FC", "ap": "AP", "app": "APp",
                           "fs": "FS", "fsp": "FSp", "fsd": "FSD", "fsdp": "FSDp"}
        achi_rank_file = {"sssp": "SSSp", "sss": "SSS", "ssp": "SSp", "ss": "SS", "sp": "Sp", "s": "S",
                          "aaa": "AAA", "aa": "AA", "a": "A", "bbb": "BBB", "bb": "BB", "b": "B",
                          "c": "C", "d": "D"}
        title_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 20, encoding="utf-8")
        achi_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 24, encoding="utf-8")
        level_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 14, encoding="utf-8")
        sin_rating_font = ImageFont.truetype("./material/typeface/Dongqing.otf", 18, encoding="utf-8")
        bg_drawer = ImageDraw.Draw(self.bg_img)
        x_gap, y_gap = (375, 120) if self.mode == "B40" else (375, 110)

        # fetch cover from database, return cover path
        def _draw_cover(id: int, x: int, y: int):
            cover_img = Image.open(BytesIO(fetch_song_cover(id))).resize((80, 80))
            self.bg_img.paste(cover_img, (x, y))

        # frame outside song cover
        def _draw_difficulty_frame(difficulty: str, x: int, y: int):
            difficulty = difficulty_file[difficulty]
            chart_frame_img = Image.open(f"./material/difficulty_frame/"
                                         f"UI_UPE_MusicJacket_Base_{difficulty}.png").resize((112, 102))
            self.bg_img.paste(chart_frame_img, (x, y), mask=chart_frame_img.split()[3])

        # AP/FC, FS/FSD
        def _draw_combo_sync_rank(combo_type: str, sync_type: str, x: int, y: int):
            if combo_type:
                combo_img = Image.open(f"./material/rate_icon/"
                                       f"UI_MSS_MBase_Icon_{combo_sync_file[combo_type]}.png").resize((28, 28))
                self.bg_img.paste(combo_img, (x, y), mask=combo_img.split()[3])
            if sync_type:
                sync_img = Image.open(f"./material/rate_icon/"
                                      f"UI_MSS_MBase_Icon_{combo_sync_file[sync_type]}.png").resize((28, 28))
                self.bg_img.paste(sync_img, (x + 24, y), mask=sync_img.split()[3])

        # 谱面类型
        def _draw_chart_type(chart_type: str, x: int, y: int):
            chart_type_img = Image.open("./material/chart_type/UI_TST_Infoicon_DeluxeMode.png").resize((50, 16)) \
                if chart_type == "DX" else \
                Image.open("./material/chart_type/UI_TST_Infoicon_StandardMode.png").resize((50, 16))
            self.bg_img.paste(chart_type_img, (x, y), mask=chart_type_img.split()[3])

        # 评级
        def _draw_achie_rank(rate: str, x: int, y: int):
            rate_img = Image.open(f"./material/achieve_rank/UI_TTR_Rank_{achi_rank_file[rate]}.png").resize((64, 30))
            self.bg_img.paste(rate_img, (x, y), mask=rate_img.split()[3])

        # 曲名标题，限长226
        def _draw_title(title: str, x: int, y: int):
            limit = lambda text: text if title_font.getsize(text)[0] <= 226 else limit(text[:-1])
            title = limit(title)
            bg_drawer.text((x, y), title, "white", font=title_font)

        # 达成率
        def _draw_achi(achi: float, x: int, y: int):
            bg_drawer.text((x, y), f"{achi:.4f}%", "white", achi_font)

        # 定数
        def _draw_inner_level(inner_level: float, x: int, y: int):
            bg_drawer.text((x - level_font.getsize(f"{inner_level} ▶")[0], y), f"{inner_level} ▶", "black", level_font)

        # 单曲 rating
        def _draw_single_rating(single_rating: int, x: int, y: int):
            bg_drawer.text((x, y), f"{single_rating}", "black", sin_rating_font)

        def _draw_old_list(queue: Queue):
            # B25/35
            x_df, y_df = (25, 232) if self.mode == "B40" else (26, 213)
            x_cover, y_cover = (41, 243) if self.mode == "B40" else (42, 224)
            x_csr, y_csr = (314, 301) if self.mode == "B40" else (315, 281)
            x_ct, y_ct = (40, 308) if self.mode == "B40" else (42, 289)
            x_ar, y_ar = (306, 267) if self.mode == "B40" else (307, 248)
            x_achi, y_achi = (140, 271) if self.mode == "B40" else (141, 252)
            x_title, y_title = (141, 237) if self.mode == "B40" else (142, 219)
            x_level, y_level = (245, 309) if self.mode == "B40" else (246, 289)
            x_sin_rating, y_sin_rating = (253, 306) if self.mode == "B40" else (254, 286)
            i = 0
            for y in range(7):
                if i >= len(self.old_list):
                    break
                for x in range(5):
                    if i >= len(self.old_list):
                        break
                    chart_info = self.old_list[i]
                    _draw_difficulty_frame(chart_info["level_label"], x_df + x * x_gap, y_df + y * y_gap)
                    _draw_cover(chart_info["song_id"], x_cover + x * x_gap, y_cover + y * y_gap)
                    _draw_combo_sync_rank(chart_info["fc"], chart_info["fs"], x_csr + x * x_gap, y_csr + y * y_gap)
                    _draw_chart_type(chart_info["type"], x_ct + x * x_gap, y_ct + y * y_gap)
                    _draw_achie_rank(chart_info["rate"], x_ar + x * x_gap, y_ar + y * y_gap)
                    _draw_title(chart_info["title"], x_title + x * x_gap, y_title + y * y_gap)
                    _draw_achi(chart_info["achievements"], x_achi + x * x_gap, y_achi + y * y_gap)
                    _draw_inner_level(chart_info["ds"], x_level + x * x_gap, y_level + y * y_gap)
                    _draw_single_rating(chart_info["ra"], x_sin_rating + x * x_gap, y_sin_rating + y * y_gap)
                    i += 1
            queue.put(1)

        def _draw_new_list(queue: Queue):
            # B15
            x_df, y_df = (25, 872) if self.mode == "B40" else (26, 1023)
            x_cover, y_cover = (41, 884) if self.mode == "B40" else (42, 1034)
            x_csr, y_csr = (314, 941) if self.mode == "B40" else (315, 1091)
            x_ct, y_ct = (40, 949) if self.mode == "B40" else (42, 1099)
            x_ar, y_ar = (306, 907) if self.mode == "B40" else (307, 1058)
            x_achi, y_achi = (140, 911) if self.mode == "B40" else (141, 1062)
            x_title, y_title = (141, 876) if self.mode == "B40" else (142, 1029)
            x_level, y_level = (245, 949) if self.mode == "B40" else (246, 1099)
            x_sin_rating, y_sin_rating = (253, 946) if self.mode == "B40" else (254, 1096)
            i = 0
            for y in range(3):
                if i >= len(self.new_list):
                    break
                for x in range(5):
                    if i >= len(self.new_list):
                        break
                    chart_info = self.new_list[i]
                    _draw_difficulty_frame(chart_info["level_label"], x_df + x * x_gap, y_df + y * y_gap)
                    _draw_cover(chart_info["song_id"], x_cover + x * x_gap, y_cover + y * y_gap)
                    _draw_combo_sync_rank(chart_info["fc"], chart_info["fs"], x_csr + x * x_gap, y_csr + y * y_gap)
                    _draw_chart_type(chart_info["type"], x_ct + x * x_gap, y_ct + y * y_gap)
                    _draw_achie_rank(chart_info["rate"], x_ar + x * x_gap, y_ar + y * y_gap)
                    _draw_title(chart_info["title"], x_title + x * x_gap, y_title + y * y_gap)
                    _draw_achi(chart_info["achievements"], x_achi + x * x_gap, y_achi + y * y_gap)
                    _draw_inner_level(chart_info["ds"], x_level + x * x_gap, y_level + y * y_gap)
                    _draw_single_rating(chart_info["ra"], x_sin_rating + x * x_gap, y_sin_rating + y * y_gap)
                    i += 1
            queue.put(1)

        Process(target=_draw_old_list, args=(queue,)).run()
        Process(target=_draw_new_list, args=(queue,)).run()

    def draw_name_plate(self, queue: Queue):
        def _draw_dxrating():
            def _specific_frame():
                if self.dx_rating < 1000:
                    return "01"
                elif self.dx_rating < 2000:
                    return "02"
                elif self.dx_rating < (3000 if self.mode == "B40" else 4000):
                    return "03"
                elif self.dx_rating < (4000 if self.mode == "B40" else 7000):
                    return "04"
                elif self.dx_rating < (5000 if self.mode == "B40" else 10000):
                    return "05"
                elif self.dx_rating < (6000 if self.mode == "B40" else 12000):
                    return "06"
                elif self.dx_rating < (7000 if self.mode == "B40" else 13000):
                    return "07"
                elif self.dx_rating < (8000 if self.mode == "B40" else 14000):
                    return "08"
                elif self.dx_rating < 8500 and self.mode == "B40":
                    return "09"
                elif self.dx_rating < 14500 and self.mode == "B50":
                    return "09"
                elif self.dx_rating < 15000 and self.mode == "B50":
                    return "10"
                else:
                    return "11"

            def _draw_rank_frame():
                if self.rank_rating == 0:
                    rank_id = "00"
                elif self.rank_rating == 250:
                    rank_id = "01"
                elif self.rank_rating == 500:
                    rank_id = "02"
                elif self.rank_rating == 750:
                    rank_id = "03"
                elif self.rank_rating == 1000:
                    rank_id = "04"
                elif self.rank_rating == 1200:
                    rank_id = "05"
                elif self.rank_rating == 1400:
                    rank_id = "06"
                elif self.rank_rating == 1500:
                    rank_id = "07"
                elif self.rank_rating == 1600:
                    rank_id = "08"
                elif self.rank_rating == 1700:
                    rank_id = "09"
                elif self.rank_rating == 1800:
                    rank_id = "10"
                elif self.rank_rating == 1850:
                    rank_id = "11"
                elif self.rank_rating == 1900:
                    rank_id = "12"
                elif self.rank_rating == 1950:
                    rank_id = "13"
                elif self.rank_rating == 2000:
                    rank_id = "14"
                else:
                    rank_id = str(int(14 + (self.rank_rating - 2000) / 10))
                rank_img = Image.open(f"./material/rank_icon/UI_Rank_{rank_id}.png").resize((100, 43))
                plate_img.paste(rank_img, (416, 9), mask=rank_img.split()[3])

            rating_frame_img = Image.open(f"./material/rating_box/"
                                          f"UI_CMN_DXRating_{_specific_frame()}.png").resize((230, 45))
            plate_img.paste(rating_frame_img, (176, 9), mask=rating_frame_img.split()[3])
            dxrating_str = reversed(str(self.dx_rating))
            for x, num in zip([355, 337, 319, 301, 283], dxrating_str):
                num_img = Image.open(f"./material/numbers/{num}.png").resize((21, 25))
                plate_img.paste(num_img, (x, 20), mask=num_img.split()[3])
            _draw_rank_frame() if self.mode == "B40" else None

            note_img = Image.open("./material/plates/UI_CMN_Shougou_Rainbow.png").resize((352, 46))
            plate_img.paste(note_img, (171, 116), mask=note_img.split()[3])
            font_note = ImageFont.truetype("./material/typeface/Dongqing.otf", 20, encoding="utf-8")
            rating_note = f"B40:  {self.rating} + {self.rank_rating}" if self.mode == "B40" else "Best 50 Simulation"
            len_x = font_note.getsize(rating_note)[0]
            plate_draw.text((171 + int((352 - len_x) / 2), 127), rating_note, "white", font=font_note,
                            stroke_width=2, stroke_fill="black")

        def _draw_name():
            white_frame_img = Image.open("./material/plates/UI_WhiteFrame.png").resize((345, 59))
            plate_img.paste(white_frame_img, (174, 59), mask=white_frame_img.split()[3])
            name_font = ImageFont.truetype("./material/typeface/SourceHanSans_17.ttf", 30, encoding="utf-8")
            nickname = ' '.join(self.nickname)
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

        plate_base = "000001.png"
        plate_img = Image.open(f"./material/plates/customized/{plate_base}")
        # from server, version plate base
        if self.plate:
            groups = match(f"({'|'.join(ver for ver in ver_num_dict.keys())})"
                           f"({'|'.join(plate for plate in plate_num_dict.keys())})?", self.plate).groups()
            plate_num = ver_num_dict[groups[0]] + plate_num_dict[groups[1]] if groups[1] else ver_num_dict[groups[0]]
            plate_num += 1 if groups[0] == "真" and groups[1] == "極" else 0
            plate_base = f"{plate_num:06d}.png"
            plate_img = Image.open(f"./material/plates/by_version/UI_Plate_{plate_base}")
        # customized plate base
        elif "qq" in self.payload:
            conn = player_dbpool.connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT PlateNo FROM PlateSetting WHERE QQId={self.payload['qq']}")
            ans = cursor.fetchone()
            plate_base = f"{ans[0]:06d}.png" if ans else plate_base
            conn.close()
            try:
                plate_img = Image.open(f"./material/plates/customized/{plate_base}") if ans else plate_img
            except FileNotFoundError:
                plate_img = Image.open(f"./material/plates/special/UI_Plate_{plate_base}") if ans else plate_img
        plate_img = plate_img.resize((1037, 167))
        plate_draw = ImageDraw.Draw(plate_img)
        _draw_name()
        _draw_dxrating()
        self.bg_img.paste(plate_img, (373, 18), mask=plate_img.split()[3])
        queue.put(1)

    def get_pic(self):
        return self.bg_img, self.error

    async def generate(self) -> bool:
        await self.get_basic_info()
        if self.mode == "B50":
            await self.get_best_50()
        queue = Queue(maxsize=3)
        self.draw_list(queue)
        Process(target=self.draw_name_plate, args=(queue,)).run()
        count = 0
        while count != 3:
            if queue.get():
                count += 1
        return True


async def get_best_pic(user_in: str, user_id: int):
    regex = r"(b|B)(4|5)0\s?(.+)?"
    _, mode, username = match(regex, user_in).groups()
    mode = "B40" if mode == '4' else "B50"
    payload = {"username": username} if username else {"qq": str(user_id)}
    payload["version"] = get_all_request_versions()
    best_list = BestList(payload, "B40") if mode == "B40" else BestList(payload, "B50")
    await best_list.generate()
    pic, error = best_list.get_pic()
    return str(image_to_base64(pic), encoding="utf-8"), error


def set_name_plate(user_in: str, user_id: int) -> str:
    regex = "设置姓名框 ([0-9]+)"
    [plate_num] = match(regex, user_in).groups()
    plate_num = int(plate_num)
    if f"{plate_num:06d}.png" in os.listdir("./material/plates/customized"):
        conn = player_dbpool.connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM PlateSetting WHERE QQId={user_id}")
        cursor.execute(f"INSERT INTO PlateSetting VALUES ({user_id},{plate_num})")
        conn.commit()
        conn.close()
        return "できました！"
    elif f"UI_Plate_{plate_num:06d}.png" in os.listdir("./material/plates/special"):
        if user_id in [993433577, 1826356872, 1873618331]:
            conn = player_dbpool.connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM PlateSetting WHERE QQId={user_id}")
            cursor.execute(f"INSERT INTO PlateSetting VALUES ({user_id},{plate_num})")
            conn.commit()
            conn.close()
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
        ans, inlist_chart = [], []
        for chart in charts:
            inlist_chart.append((chart["song_id"], chart["level_label"]))
        # 未到达 SSS+ 的推荐升1评级
        for chart in charts:
            if chart['achievements'] < 100.5:
                for i, aim_achi in enumerate(achie_ranks.values()):
                    if chart['achievements'] >= aim_achi:
                        break
                aim_achi = tuple(achie_ranks.values())[i - 1]
                ans.append(f"{difficulty_short[chart['level_index']]}{chart['ds']}  {chart['song_id']}  "
                           f"{chart['title']}  {aim_achi}%  "
                           f"Rating +{_cal_single_rating(aim_achi, chart['ds']) - chart['ra']}")
        # 获取平均单曲 rating，计算对应定数达成率
        level_achi_list = _rating_to_inner_level(charts[-1]['ra'])
        conn = mai_dbpool.connection()
        cursor = conn.cursor()
        for achi, level in level_achi_list:
            # 固定达成率，提高定数
            if mode == "B25":
                cursor.execute(f"SELECT CD.InnerLevel,CD.Difficulty,SI.Id,SI.Title FROM ChartDifficulty CD "
                               f"JOIN SongInfo SI ON CD.Id=SI.Id WHERE CD.InnerLevel BETWEEN {level + 0.2} AND "
                               f"{level + 0.4} AND CD.Version='舞萌DX 2021' AND SI.ChinaVersion!='舞萌DX 2021'")
            else:
                cursor.execute(f"SELECT CD.InnerLevel,CD.Difficulty,SI.Id,SI.Title FROM ChartDifficulty CD "
                               f"JOIN SongInfo SI ON CD.Id=SI.Id WHERE CD.InnerLevel BETWEEN {level + 0.2} AND "
                               f"{level + 0.4} AND CD.Version='舞萌DX 2021' AND SI.ChinaVersion='舞萌DX 2021'")
            recommend_charts = cursor.fetchall()
            ans += [f"{_get_difficulty_short(chart[1])}{chart[0]}  {chart[2]}  {chart[3]}  " \
                    f"{achi}%  Rating +{_cal_single_rating(achi, chart[0]) - charts[-1]['ra']}"
                    for chart in recommend_charts if (chart[2], chart[1]) not in inlist_chart if achi >= 97]
            # 固定或降低定数，提高一档达成率
            if mode == "B25":
                cursor.execute(f"SELECT CD.InnerLevel,CD.Difficulty,SI.Id,SI.Title FROM ChartDifficulty CD "
                               f"JOIN SongInfo SI ON CD.Id=SI.Id WHERE CD.InnerLevel BETWEEN {level - 0.1} AND "
                               f"{level + 0.1} AND CD.Version='舞萌DX 2021' AND SI.ChinaVersion!='舞萌DX 2021'")
            else:
                cursor.execute(f"SELECT CD.InnerLevel,CD.Difficulty,SI.Id,SI.Title FROM ChartDifficulty CD "
                               f"JOIN SongInfo SI ON CD.Id=SI.Id WHERE CD.InnerLevel BETWEEN {level - 0.1} AND "
                               f"{level + 0.1} AND CD.Version='舞萌DX 2021' AND SI.ChinaVersion='舞萌DX 2021'")
            recommend_charts = cursor.fetchall()
            if achi < 100.5:
                for i, aim_achi in enumerate(achie_ranks.values()):
                    if achi >= aim_achi:
                        break
                aim_achi = tuple(achie_ranks.values())[i - 1]
                for chart in recommend_charts:
                    if (chart[2], chart[1]) not in inlist_chart:
                        ans += [f"{_get_difficulty_short(chart[1])}{chart[0]}  {chart[2]}  {chart[3]}  {aim_achi}% "
                                f" Rating +{_cal_single_rating(aim_achi, chart[0]) - charts[-1]['ra']}"]
        conn.close()
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
    payload["version"] = get_all_request_versions()
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
