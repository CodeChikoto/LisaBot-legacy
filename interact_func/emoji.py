import os
import random

mom_quotation = {"care": ["どうしたの？", "大丈夫？", "お元気ですか？"],
                 "sugar": ["ゆきなのこと......", "ゆきな〜"]}


def mom(key: str):
    ans_list = mom_quotation[key]
    return ans_list[random.randint(0, len(ans_list) - 1)]


def random_emoji(name: str):
    dir = os.listdir("emoji/" + name)
    emoji = random.sample(dir, 1)[0]
    emoji_path = f"file://{os.getcwd()}/emoji/{name}/{emoji}"
    return emoji_path
