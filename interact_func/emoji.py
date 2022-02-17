import os

from tools.shared_var import *
import random


random.seed(2301)
mom_quotation = {"care": ["どうしたの？", "大丈夫？", "お元気ですか？"],
                 "sugar": ["ゆきなのこと......", "ゆきな〜"]}


def mom(key: str):
    ans_list = mom_quotation[key]
    return ans_list[random.randint(0, len(ans_list) - 1)]


def random_emoji(type: str):
    conn = quotation_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Type,Image,ImageExt FROM Emoji WHERE Type LIKE '{type}'")
    res = cursor.fetchall()
    [[type, image, ext]] = random.sample(res, 1)
    with open(f"./cache/{type}{ext}", "wb") as file:
        file.write(image)
    return f"file://{os.getcwd()}/cache/{type}{ext}"


def select_emoji(id: int):
    conn = quotation_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Type,Image,ImageExt FROM Emoji WHERE Id={id}")
    type, image, ext = cursor.fetchone()
    with open(f"./cache/{type}{ext}", "wb") as file:
        file.write(image)
    return f"file://{os.getcwd()}/cache/{type}{ext}"