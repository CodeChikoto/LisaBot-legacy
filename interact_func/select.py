import re
import random

random.seed("20211104")


def auto_select(user_in: str) -> str:
    choices = re.split("or|还是|或者", re.split(" ", user_in, 1)[1])
    for choice in choices:
        if re.search("听夏洛缇", choice):
            return choice + "にすればいいよよ！"
    rand_num = random.randint(-1, len(choices))
    if 0 <= rand_num < len(choices):
        return choices[rand_num] + "にすればいいよ！"
    elif rand_num == -1:
        return "全不にすればいいよ！"
    else:
        return "全部にすればいいよ！"
