import re
from interact_func.send_help import *
import random
import os
from tools.database import *
import time


random.seed(time.time())


def get_ans(id: str):
    cursor = Cursor()
    cursor.execute(f"SELECT Id,Title,Image,ImageExt "
                   f"FROM SongInfo WHERE Id='{id}'")
    id, title, image, image_ext = cursor.fetchone()
    with open("./temp" + image_ext, "wb") as cover:
        cover.write(image)
    cover.close()
    return id, title, "./temp" + image_ext


def tip_basic_info(id: str):
    cursor = Cursor()
    cursor.execute(f"SELECT Artist,BPM,Genre,ChartType,Version "
                   f"FROM SongInfo WHERE Id='{id}'")
    res = cursor.fetchone()
    return f"艺术家是 {res[0]} 哦", f"这首歌 BPM 是{res[1]}", f"这张是{res[3]}谱面", \
           f"分类是 {res[2]}", f"歌曲于 {res[4]} 加入 maimai～！"


def tip_chart(id: str):
    cursor = Cursor()
    cursor.execute(f"SELECT Level FROM ChartInfo WHERE Id='{id}' "
                   f"AND Difficulty IN ('Expert','Master','Re:Master')")
    res = cursor.fetchall()
    if len(res) == 3:
        return f"这首歌有 Re:Master", f"这首歌 Expert {res[0]}", \
               f"这首歌 Master {res[1]}", f"这首歌 Re:Master {res[2]}"
    else:
        return f"这首歌没有 Re:Master", f"这首歌 Expert {res[0]}", \
               f"这首歌 Master {res[1]}"
