import os
from io import BytesIO
from PIL import Image
from tools.image import image_to_base64
from tools.shared_var import *
import random


random.seed(2301)
mom_quotation = {"care": ["どうしたの？", "大丈夫？", "お元気ですか？"],
                 "sugar": ["ゆきなのこと......", "ゆ～き～な〜"]}


def mom(key: str):
    ans_list = mom_quotation[key]
    return ans_list[random.randint(0, len(ans_list) - 1)]


def random_emoji(type: str):
    conn = quotation_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Image FROM Emoji WHERE Type LIKE '{type}'")
    res = cursor.fetchall()
    img = random.choice(res)
    return str(image_to_base64(Image.open(BytesIO(img))), encoding="utf-8")


def select_emoji(id: int):
    conn = quotation_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Image FROM Emoji WHERE Id={id}")
    [img] = cursor.fetchone()
    return str(image_to_base64(Image.open(BytesIO(img))), encoding="utf-8")