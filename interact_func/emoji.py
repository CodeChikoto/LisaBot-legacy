import os
from io import BytesIO
from PIL import Image

from models.quotation_models import Emoji
from tools.image import image_to_base64
from tools.shared_var import *
import random


random.seed(2301)
mom_quotation = ["どうしたの？", "大丈夫？", "お元気ですか？", "ゆきなのこと......", "ゆ～き～な〜", "はいはい〜",
                 "おクーキーどぞ！", "哇哦～"]


def mom():
    return random.choice(mom_quotation)


def random_emoji(type: str):
    emojis = Emoji.select(Emoji.image).where((Emoji.type_ ** type) & (Emoji.bot_name == "Lisa")).objects()
    img = random.choice(emojis).image
    return str(image_to_base64(Image.open(BytesIO(img))), encoding="utf-8")


def select_emoji(id: int):
    emojis = Emoji.get(Emoji.id == id)
    return str(image_to_base64(Image.open(BytesIO(emojis.image))), encoding="utf-8")