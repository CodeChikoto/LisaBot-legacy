import re
import random

random.seed("20211104")


def auto_select(user_in: str) -> str:
    choices = re.split("or|还是|或者", user_in)
    for choice in choices:
        if re.search("听夏洛缇", choice):
            return choice + "ばいいよ！"
    rand_num = random.randint(0, len(choices) - 1)
    return choices[rand_num] + "ばいいよ！"
