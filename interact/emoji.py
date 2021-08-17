from nonebot import on_command, on_regex, on_notice
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
import os
import random


hit_emoji_dir = "emoji/hit/"


def hit_person():
    dir = os.listdir(hit_emoji_dir)
    amount = len(dir)
    emoji = random.sample(dir, 1)[0]
    file_path = f"file://{os.getcwd()}/{hit_emoji_dir}/{emoji}"
    msg = Message([
        {
            "type": "image",
            "data": {"file": f"{file_path}"}
        }
    ])
    return msg


hit_person()