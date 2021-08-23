import os
import random


hit_emoji_dir = "emoji/hit/"
mom_quotation = {"care": ["どうしたの？", "大丈夫？", "お元気ですか？"],
                 "sugar": ["ゆきなのこと......", "ゆきな〜"]}


def hit_person():
    dir = os.listdir(hit_emoji_dir)
    emoji = random.sample(dir, 1)[0]
    emoji_path = f"file://{os.getcwd()}/{hit_emoji_dir}/{emoji}"
    return emoji_path


def mom(key: str):
    ans_list = mom_quotation[key]
    return ans_list[random.randint(0, len(ans_list) - 1)]