from typing import *

import requests
from PIL import Image, ImageDraw, ImageFont
from tools.database import database_pool
from tools.get_data_func import *
from re import match
from tools.image import image_to_base64
from tools.shared_var import *
import _thread


class BestList():
    def __init__(self, payload: dict, mode: str):
        self.rank_rating = 0
        self.nickname = ""
        self.rating = 0
        self.payload = payload
        self.mode = mode
        self.bg_path = "./material/B40.png" if self.mode == "B40" \
            else "./material/B50.png"
        self.bg_img = Image.open(self.bg_path)
        self.bg_draw = ImageDraw.Draw(self.bg_img)
        self.old_list, self.new_list = [], []
        self.basic_info = {}
        self.dx_rating = 0
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
        achi_rank_coef = {"SSS+": 22.4, "SSS": 21.6, "SS+": 21.1, "SS": 20.8, "S+": 20.3, "S": 20.0,
                          "AAA": 16.8, "AA": 15.2, "A": 13.6, "BBB": 12.0, "BB": 11.2, "B": 9.6,
                          "C": 8.0, "D": 0}

        def _cal_single_rating(achi: float, inner_level: float) -> (int, str):
            achi_rank = None
            for achi_rank_trial in achie_ranks.keys():
                if achi >= achie_ranks[achi_rank_trial]:
                    achi_rank = achi_rank_trial
                    break
            achi = 100.5 if achi > 100.5 else achi
            return int(achi / 100 * achi_rank_coef[achi_rank] * float(inner_level)), \
                   achi_rank.lower().replace('+', 'p')

        def _fill_info(start: int, end: int, lock):
            nonlocal charts
            index_to_str = {0: "Basic", 1: "Advanced", 2: "Expert", 3: "Master", 4: "Re:MASTER"}
            conn = database_pool.connection()
            cursor = conn.cursor()
            for chart in charts[start:end]:
                difficulty = index_to_str[chart["level_index"]]
                title_rep = chart["title"].replace("'", "\\'")
                cursor.execute(f"SELECT Id,InnerLevel FROM ChartDifficulty WHERE Id IN "
                               f"(SELECT Id FROM SongInfo WHERE Title='{title_rep}' AND ChartType='{chart['type']}') "
                               f"AND Difficulty='{difficulty}' AND Version='舞萌DX 2021'")
                [id, inner_level] = cursor.fetchone()
                chart["ds"] = float(inner_level)
                chart["ra"], chart["rate"] = _cal_single_rating(chart["achievements"], inner_level)
                chart["level_label"], chart["song_id"] = difficulty, id
            conn.close()
            lock.release()

        data = await get_player_data(self.payload, "plate")
        if isinstance(data, dict):
            charts, clear = data["verlist"], len(data["verlist"])
            locks_list = []
            for i in range(4):
                lock = _thread.allocate_lock()
                lock.acquire()
                locks_list.append(lock)
            for i in range(4):
                _thread.start_new_thread(_fill_info, (int(clear / 4 * i), int(clear / 4 * (i + 1)), locks_list[i]))
            while any(lock.locked() for lock in locks_list):
                pass
            charts.sort(key=lambda x: x["ra"], reverse=True)
            self.old_list, self.new_list = [], []
            for chart in charts:
                if len(self.old_list) == 35 and len(self.new_list) == 15:
                    break
                if chart["song_id"] not in new_id_list and len(self.old_list) < 35:
                    self.old_list.append(chart)
                elif chart["song_id"] in new_id_list and len(self.new_list) < 15:
                    self.new_list.append(chart)
            self.dx_rating = self.rating = sum(chart["ra"] for chart in self.old_list + self.new_list)
            return True
        else:
            self.error = data
            return False

    def draw_list(self):
        difficulty_file = {"Basic": "BSC", "Advanced": "ADV", "Expert": "EXP", "Master": "MST",
                            "Re:MASTER": "MST_Re"}
        ranks_alias = {"fcp": "FCp", "fc": "FC", "ap": "AP", "app": "APp",
                       "fs": "FS", "fsp": "FSp", "fsd": "FSD", "fsdp": "FSDp"}
        achi_rank_file = {"sssp": "SSSp", "sss": "SSS", "ssp": "SSp", "ss": "SS", "sp": "Sp", "s": "S",
                          "aaa": "AAA", "aa": "AA", "a": "A", "bbb": "BBB", "bb": "BB", "b": "B",
                          "c": "C", "d": "D"}
        title_font = ImageFont.truetype("./SourceHanSans_17.ttf", (24 if self.mode == "B40" else 20), encoding="utf-8")
        whole_font = ImageFont.truetype("./Dongqing.otf", 40, encoding="utf-8")
        deci_font = ImageFont.truetype("./Dongqing.otf", 24, encoding="utf-8")
        achi_font = ImageFont.truetype("./Dongqing.otf", 24, encoding="utf-8")
        level_font = ImageFont.truetype("./Dongqing.otf", (16 if self.mode == "B40" else 13), encoding="utf-8")
        rate_font = ImageFont.truetype("./Dongqing.otf", (24 if self.mode == "B40" else 18), encoding="utf-8")
        bg_drawer = ImageDraw.Draw(self.bg_img)
        x_gap, y_gap = (480, 175) if self.mode == "B40" else (375, 115)

        # fetch cover from database, return cover path
        def _draw_cover(id: int, x: int, y: int, cursor):
            cursor.execute(f"SELECT Cover,ImageExt FROM SongInfo WHERE Id={id}")
            [cover_blob, ext] = cursor.fetchone()
            # resp = cursor.fetchone()
            with open("./cache/" + str(id) + ext, "wb") as cover_file:
                cover_file.write(cover_blob)
            cover_file.close()
            cover_img = Image.open("./cache/" + str(id) + ext).convert("RGB")
            cover_img = cover_img.resize((130, 130)) if self.mode == "B40" \
                else cover_img.resize((80, 80))
            self.bg_img.paste(cover_img, (x, y))

        # frame outside song cover
        def _draw_chart_frame(difficulty: str, x: int, y: int):
            difficulty = difficulty_file[difficulty]
            chart_frame_img = Image.open(f"./material/UI_UPE_MusicJacket_Base_{difficulty}.png")
            chart_frame_img = chart_frame_img.resize((188, 171)) if self.mode == "B40" \
                else chart_frame_img.resize((115, 105))
            self.bg_img.paste(chart_frame_img, (x, y), mask=chart_frame_img.split()[3])

        # AP/FC, FS/FSD
        def _draw_combo_sync_rank(combo_type: str, sync_type: str, x: int, y: int):
            if combo_type:
                combo_img = Image.open(f"./material/UI_MSS_MBase_Icon_{ranks_alias[combo_type]}.png")
                combo_img = combo_img.resize((40, 40)) if self.mode == "B40" \
                    else combo_img.resize((28, 28))
                self.bg_img.paste(combo_img, (x, y), mask=combo_img.split()[3])
            if sync_type:
                sync_img = Image.open(f"./material/UI_MSS_MBase_Icon_{ranks_alias[sync_type]}.png")
                sync_img = sync_img.resize((40, 40)) if self.mode == "B40" \
                    else sync_img.resize((28, 28))
                self.bg_img.paste(sync_img, (x + (36 if self.mode == "B40" else 24), y), mask=sync_img.split()[3])

        # 谱面类型
        def _draw_chart_type(chart_type: str, x: int, y: int):
            chart_type_img = Image.open("./material/UI_TST_Infoicon_DeluxeMode.png") \
                if chart_type == "DX" else Image.open("./material/UI_TST_Infoicon_StandardMode.png")
            chart_type_img = chart_type_img.resize((70, 22)) if self.mode == "B40" \
                else chart_type_img.resize((50, 16))
            self.bg_img.paste(chart_type_img, (x, y), mask=chart_type_img.split()[3])

        # 评级
        def _draw_achie_rank(rate: str, x: int, y: int):
            rate_img = Image.open(f"./material/UI_GAM_Rank_{achi_rank_file[rate]}.png")
            rate_img = rate_img.resize((100, 40)) if self.mode == "B40" \
                else rate_img.resize((70, 28))
            self.bg_img.paste(rate_img, (x, y), mask=rate_img.split()[3])

        # 曲名标题，限长272/226
        def _draw_title(title: str, x: int, y: int):
            max_len = 272 if self.mode == "B40" else 226
            len_x = title_font.getsize(title)[0]
            if len_x > max_len:
                title = title[:int(max_len / len_x * len(title))]
            bg_drawer.text((x, y), title, "white", font=title_font)

        # B40 完成率，whole 整数部分，deci 小数部分
        def _draw_achi_40(achi: float, x1: int, y1: int, x2: int, y2: int):
            whole, deci = f"{achi:.4f}".split('.')
            whole += '.'
            deci += '%'
            whole_len = whole_font.getsize(whole)[0]
            bg_drawer.text((x1 - whole_len, y1), whole, "white", whole_font)
            bg_drawer.text((x2, y2), deci, "white", deci_font)

        # B50 完成率，整数小数统一大小
        def _draw_achi_50(achi: float, x: int, y: int):
            bg_drawer.text((x, y), f"{achi:.4f}%", "white", achi_font)

        # 定数和单曲得分
        def _draw_level_rate(inner_level: float, x1: int, y1: int, rate: int, x2: int, y2: int):
            level_str = f"{inner_level} > "
            level_str_len = level_font.getsize(level_str)[0]
            bg_drawer.text((x1 - level_str_len, y1), level_str, "black", level_font)
            bg_drawer.text((x2, y2), f"{rate}", "black", rate_font)

        def _draw_old_list(lock):
            # B25/35
            x_cf, y_cf = (14, 280) if self.mode == "B40" else (24, 212)
            x_cover, y_cover = (43, 303) if self.mode == "B40" else (42, 226)
            x_csr, y_csr = (403, 399) if self.mode == "B40" else (315, 281)
            x_ct, y_ct = (41, 413) if self.mode == "B40" else (40, 292)
            x_ar, y_ar = (391, 348) if self.mode == "B40" else (306, 250)
            x_title, y_title = (199, 300) if self.mode == "B40" else (142, 219)
            x1_lr, y1_lr, x2_lr, y2_lr = (327, 412, 336, 405) if self.mode == "B40" else (246, 289, 252, 285)
            conn = database_pool.connection()
            cursor = conn.cursor()
            i = 0
            for y in range(7):
                if i >= len(self.old_list):
                    break
                for x in range(5):
                    if i >= len(self.old_list):
                        break
                    chart_info = self.old_list[i]
                    _draw_chart_frame(chart_info["level_label"], x_cf + x * x_gap, y_cf + y * y_gap)
                    _draw_cover(chart_info["song_id"], x_cover + x * x_gap, y_cover + y * y_gap, cursor)
                    _draw_combo_sync_rank(chart_info["fc"], chart_info["fs"], x_csr + x * x_gap, y_csr + y * y_gap)
                    _draw_chart_type(chart_info["type"], x_ct + x * x_gap, y_ct + y * y_gap)
                    _draw_achie_rank(chart_info["rate"], x_ar + x * x_gap, y_ar + y * y_gap)
                    _draw_title(chart_info["title"], x_title + x * x_gap, y_title + y * y_gap)
                    if self.mode == "B40":
                        _draw_achi_40(chart_info["achievements"], 295 + x * x_gap, 346 + y * y_gap,
                                      298 + x * x_gap, 360 + y * y_gap)
                    else:
                        _draw_achi_50(chart_info["achievements"], 143 + x * x_gap, 252 + y * y_gap)
                    _draw_level_rate(chart_info["ds"], x1_lr + x * x_gap, y1_lr + y * y_gap,
                                     chart_info["ra"], x2_lr + x * x_gap, y2_lr + y * y_gap)
                    i += 1
            conn.close()
            lock.release()

        def _draw_new_list(lock):
            # B15
            x_cf, y_cf = (14, 1227) if self.mode == "B40" else (24, 1051)
            x_cover, y_cover = (43, 1250) if self.mode == "B40" else (42, 1065)
            x_csr, y_csr = (403, 1346) if self.mode == "B40" else (315, 1120)
            x_ct, y_ct = (41, 1360) if self.mode == "B40" else (40, 1131)
            x_ar, y_ar = (391, 1295) if self.mode == "B40" else (306, 1089)
            x_title, y_title = (199, 1247) if self.mode == "B40" else (142, 1058)
            x1_lr, y1_lr, x2_lr, y2_lr = (327, 1359, 336, 1352) if self.mode == "B40" else (246, 1128, 252, 1124)
            i = 0
            conn = database_pool.connection()
            cursor = conn.cursor()
            for y in range(3):
                if i >= len(self.new_list):
                    break
                for x in range(5):
                    if i >= len(self.new_list):
                        break
                    chart_info = self.new_list[i]
                    _draw_chart_frame(chart_info["level_label"], x_cf + x * x_gap, y_cf + y * y_gap)
                    _draw_cover(chart_info["song_id"], x_cover + x * x_gap, y_cover + y * y_gap, cursor)
                    _draw_combo_sync_rank(chart_info["fc"], chart_info["fs"], x_csr + x * x_gap, y_csr + y * y_gap)
                    _draw_chart_type(chart_info["type"], x_ct + x * x_gap, y_ct + y * y_gap)
                    _draw_achie_rank(chart_info["rate"], x_ar + x * x_gap, y_ar + y * y_gap)
                    _draw_title(chart_info["title"], x_title + x * x_gap, y_title + y * y_gap)
                    if self.mode == "B40":
                        _draw_achi_40(chart_info["achievements"], 295 + x * x_gap, 1293 + y * y_gap,
                                      298 + x * x_gap, 1307 + y * y_gap)
                    else:
                        _draw_achi_50(chart_info["achievements"], 143 + x * x_gap, 1091 + y * y_gap)
                    _draw_level_rate(chart_info["ds"], x1_lr + x * x_gap, y1_lr + y * y_gap,
                                     chart_info["ra"], x2_lr + x * x_gap, y2_lr + y * y_gap)
                    i += 1
            conn.close()
            lock.release()

        lock1, lock2 = _thread.allocate_lock(), _thread.allocate_lock()
        lock1.acquire(), lock2.acquire()
        _thread.start_new_thread(_draw_old_list, (lock1,))
        _thread.start_new_thread(_draw_new_list, (lock2,))
        while lock1.locked() or lock2.locked():
            pass
    
    def draw_name_plate(self):
        pass
    
    def draw_dxrating(self):
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
            rank_img = Image.open(f"./material/UI_Rank_{rank_id}.png")
            rank_img = rank_img.resize((100, 43))
            self.bg_img.paste(rank_img, (790, 28), mask=rank_img.split()[3])

        rating_frame_img = Image.open(f"./material/UI_CMN_DXRating_{_specific_frame()}.png")
        rating_frame_img = rating_frame_img.resize((226, 44))
        self.bg_img.paste(rating_frame_img, (550, 28), mask=rating_frame_img.split()[3])
        dxrating_str = reversed(str(self.dx_rating))
        for x, num in zip([725, 708, 690, 672, 655], dxrating_str):
            num_img = Image.open(f"./material/{num}.png")
            num_img = num_img.resize((21, 25))
            self.bg_img.paste(num_img, (x, 38), mask=num_img.split()[3])
        _draw_rank_frame() if self.mode == "B40" else None

        font_note = ImageFont.truetype("./Dongqing.otf", 20, encoding="utf-8")
        rating_note = f"B40:  {self.rating} + {self.rank_rating}" \
            if self.mode == "B40" else ""
        len_x = font_note.getsize(rating_note)[0]
        self.bg_draw.text((544 + int((353 - len_x) / 2), 144), rating_note, "white", font=font_note,
                          stroke_width=2, stroke_fill="black")

    def draw_name(self):
        name_font = ImageFont.truetype("./SourceHanSans_17.ttf", 30, encoding="utf-8")
        nickname = ' '.join(self.nickname)
        len_x = name_font.getsize(nickname)[0]
        if len_x > 271:
            nickname = nickname[:int(271 / len_x * len(nickname))]
        self.bg_draw.text((567, 80), nickname, "black", name_font)
        if "qq" in self.payload:
            try:
                data = requests.get(f'http://q1.qlogo.cn/g?b=qq&nk={self.payload["qq"]}&s=640')
                with open(f"./cache/head{self.payload['qq']}.png", "wb") as head_file:
                    head_file.write(data.content)
                head_img = Image.open(f"./cache/head{self.payload['qq']}.png")
                head_img = head_img.resize((143, 143))
                head_img_mask = Image.open(f"./material/UI_Icon_000001.png")
                head_img_mask = head_img_mask.resize((143, 143))
                self.bg_img.paste(head_img, (385, 29), mask=head_img_mask)
            finally:
                pass

    def get_pic(self):
        return self.bg_img, self.error

    async def generate(self) -> bool:
        def _draw_others(lock):
            self.draw_dxrating()
            self.draw_name()
            lock.release()

        await self.get_basic_info()
        if self.mode == "B50":
            await self.get_best_50()
        lock = _thread.allocate_lock()
        lock.acquire()
        _thread.start_new_thread(_draw_others, (lock,))
        self.draw_list()
        while lock.locked():
            pass
        return True


async def get_best_pic(user_in: str, user_id: int):
    regex = r"(b|B)(4|5)0\s?(.+)?"
    _, mode, username = match(regex, user_in).groups()
    mode = "B40" if mode == '4' else "B50"
    payload = {"username": username} if username else {"qq": str(user_id)}
    payload["version"] = list(set(version for version in version_alias.values()))
    if mode == "B40":
        best_list = BestList(payload, "B40")
    else:
        best_list = BestList(payload, "B50")
    await best_list.generate()
    pic, error = best_list.get_pic()
    return str(image_to_base64(pic), encoding="utf-8"), error
